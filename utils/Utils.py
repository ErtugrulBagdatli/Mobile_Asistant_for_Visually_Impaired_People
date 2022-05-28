import cv2

import numpy as np
import tensorflow as tf
import keras.backend as K


def load_weights(model, weight_file):
    wf = open(weight_file, 'rb')

    major, minor, revision, seen, _ = np.fromfile(wf, dtype=np.int32, count=5)
    j = 0
    for i in range(75):
        conv_layer_name = 'conv2d_%d' % i if i > 0 else 'conv2d'
        bn_layer_name = 'batch_normalization_%d' % j if j > 0 else 'batch_normalization'

        conv_layer = model.get_layer(conv_layer_name)
        filters = conv_layer.filters
        k_size = conv_layer.kernel_size[0]
        in_dim = conv_layer.input_shape[-1]

        if i not in [58, 66, 74]:
            # darknet weights: [beta, gamma, mean, variance]
            bn_weights = np.fromfile(wf, dtype=np.float32, count=4 * filters)
            bn_weights = bn_weights.reshape((4, filters))[[1, 0, 2, 3]]
            bn_layer = model.get_layer(bn_layer_name)

            j += 1

        else:
            conv_bias = np.fromfile(wf, dtype=np.float32, count=filters)

        # darknet shape is (out_dim, in_dim, height,width)
        conv_shape = (filters, in_dim, k_size, k_size)
        conv_weights = np.fromfile(wf, dtype=np.float32, count=np.product(conv_shape))

        # tf shpae (height, width, in_dim, out_dim)
        conv_weights = conv_weights.reshape(conv_shape).transpose([2, 3, 1, 0])

        if i not in [58, 66, 74]:
            conv_layer.set_weights([conv_weights])
            bn_layer.set_weights(bn_weights)
        else:
            conv_layer.set_weights([conv_weights, conv_bias])

    assert len(wf.read(0)) == 0, 'failed to read all data'
    wf.close()

    return model


def read_class_names(class_file_name):
    names = {}
    with open(class_file_name, 'r') as data:
        for ID, name in enumerate(data):
            names[ID] = name.strip('\n')
    return names


def transform_images(x_train, size):
    x_train = tf.image.resize(x_train, (size, size))
    x_train = x_train / 255
    return x_train


def box_detector(pred):
    center_x, center_y, width, height, confidence, classes = tf.split(pred, [1, 1, 1, 1, 1, -1], axis=-1)
    top_left_x = (center_x - width / 2.) / 416
    top_left_y = (center_y - height / 2.0) / 416.0
    bottom_right_x = (center_x + width / 2.0) / 416.0
    bottom_right_y = (center_y + height / 2.0) / 416.0

    boxes = tf.concat([top_left_y, top_left_x, bottom_right_y, bottom_right_x], axis=-1)
    scores = confidence * classes
    scores = np.array(scores)

    scores = scores.max(axis=-1)
    class_index = np.argmax(classes, axis=-1)

    final_indexes = tf.image.non_max_suppression(boxes, scores, max_output_size=20)
    final_indexes = np.array(final_indexes)
    class_names = class_index[final_indexes]
    boxes = np.array(boxes)
    scores = np.array(scores)
    class_names = np.array(class_names)
    boxes = boxes[final_indexes, :]

    scores = scores[final_indexes]
    boxes = boxes * 416

    return boxes, class_names, scores


def drawbox(boxes, class_names, scores, names, img):
    data = np.concatenate([boxes, scores[:, np.newaxis], class_names[:, np.newaxis]], axis=-1)
    data = data[np.logical_and(data[:, 0] >= 0, data[:, 0] <= 416)]
    data = data[np.logical_and(data[:, 1] >= 0, data[:, 1] <= 416)]
    data = data[np.logical_and(data[:, 2] >= 0, data[:, 2] <= 416)]
    data = data[np.logical_and(data[:, 3] >= 0, data[:, 3] <= 416)]
    data = data[data[:, 4] > 0.3]

    img = cv2.resize(img, (416, 416))
    for i, row in enumerate(data):
        img = cv2.rectangle(img, (int(row[1]), int(row[0])), (int(row[3]), int(row[2])), (170, 1, 130), 1)
        img = cv2.putText(img, (list(names.keys())[int(row[5])] + ": " + "{:.2f}".format(row[4])),
                          (int(row[1]), int(row[0] - 5)),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)

    return img


def iou(box1, box2):
    intersect_x_min = np.max([box1[0], box2[0]])
    intersect_y_min = np.max([box1[1], box2[1]])
    intersect_x_max = np.min([box1[2], box2[2]])
    intersect_y_max = np.min([box1[3], box2[3]])

    intersect_area = (intersect_x_max - intersect_x_min) * (intersect_y_max - intersect_y_min)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    iou_score = intersect_area / (box1_area + box2_area - intersect_area)

    return iou_score


def iou_batch_array(actual, pred):
    '''
    Parameters
    ----------
    box: shape(batch,n,n,3,4)s


    Returns
    --------
    iou_score: shape(batch,n,n,3)
    '''

    box1 = []
    box2 = []

    box1.append(actual[..., 0:1] - actual[..., 2:3] / 2)
    box1.append(actual[..., 1:2] - actual[..., 3:4] / 2)
    box1.append(actual[..., 0:1] + actual[..., 2:3] / 2)
    box1.append(actual[..., 1:2] + actual[..., 3:4] / 2)
    box2.append(pred[..., 0:1] - pred[..., 2:3] / 2)
    box2.append(pred[..., 1:2] - pred[..., 3:4] / 2)
    box2.append(pred[..., 0:1] + pred[..., 2:3] / 2)
    box2.append(pred[..., 1:2] + pred[..., 3:4] / 2)

    box1 = tf.stack(box1, axis=-1)
    box2 = tf.stack(box2, axis=-1)

    intersect_x_min = K.maximum(box1[..., 0], box2[..., 0])
    intersect_y_min = K.maximum(box1[..., 1], box2[..., 1])
    intersect_x_max = K.minimum(box1[..., 2], box2[..., 2])
    intersect_y_max = K.minimum(box1[..., 3], box2[..., 3])

    intersect_area = (intersect_x_max - intersect_x_min) * (intersect_y_max - intersect_y_min)

    box1_area = (box1[..., 2] - box1[..., 0]) * (box1[..., 3] - box1[..., 1])
    box2_area = (box2[..., 2] - box2[..., 0]) * (box2[..., 3] - box2[..., 1])

    iou_score = intersect_area / (box1_area + box2_area - intersect_area)

    return iou_score
