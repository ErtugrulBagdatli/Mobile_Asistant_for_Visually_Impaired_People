import time
from time import time

import matplotlib.pyplot as plt
import requests
import tensorflow.keras.backend as K
from absl import logging
from tensorflow.keras.layers import BatchNormalization
from tensorflow.keras.losses import MeanSquaredError, BinaryCrossentropy, CategoricalCrossentropy
from tensorflow.keras.losses import binary_crossentropy
import tensorflow as tf


def convolutional(input_layer, filters_shape, down_sample=False,
                  activate=True, batch_norm=True, regularization=0.0005, reg_stddev=0.01, activate_alpha=0.1):
    if down_sample:
        input_layer = tf.keras.layers.ZeroPadding2D(((1, 0), (1, 0)))(input_layer)
        padding = "valid"
        strides = 2
    else:
        padding = "same"
        strides = 1

    conv = tf.keras.layers.Conv2D(filters=filters_shape[-1],
                                  kernel_size=filters_shape[0],
                                  strides=strides,
                                  padding=padding,
                                  use_bias=not batch_norm,
                                  kernel_regularizer=tf.keras.regularizers.l2(regularization),
                                  kernel_initializer=tf.random_normal_initializer(stddev=reg_stddev),
                                  bias_initializer=tf.constant_initializer(0.)
                                  )(input_layer)

    if batch_norm:
        conv = BatchNormalization()(conv)
    if activate:
        conv = tf.nn.leaky_relu(conv, alpha=activate_alpha)

    return conv


# Output = Input + Conv + Conv
def res_block(input_layer, filter_num1, filter_num2):
    short_cut = input_layer
    conv = convolutional(input_layer, filters_shape=(1, 1, input_layer, filter_num1))
    conv = convolutional(conv, filters_shape=(3, 3, filter_num1, filter_num2))

    res_output = short_cut + conv
    return res_output


def darknet_53(input_data):
    input_data = convolutional(input_data, (3, 3, 3, 32))
    input_data = convolutional(input_data, (3, 3, 32, 64), down_sample=True)

    for i in range(1):
        input_data = res_block(input_data, 32, 64)

    input_data = convolutional(input_data, (3, 3, 64, 128), down_sample=True)

    for i in range(2):
        input_data = res_block(input_data, 64, 128)

    input_data = convolutional(input_data, (3, 3, 128, 256), down_sample=True)

    for i in range(8):
        input_data = res_block(input_data, 128, 256)

    route_1 = input_data

    input_data = convolutional(input_data, (3, 3, 256, 512), down_sample=True)

    for i in range(8):
        input_data = res_block(input_data, 256, 512)
    route_2 = input_data
    input_data = convolutional(input_data, (3, 3, 512, 1024), down_sample=True)

    for i in range(4):
        input_data = res_block(input_data, 512, 1024)

    return route_1, route_2, input_data


def upsample(input_layer):
    return tf.image.resize(input_layer, (input_layer.shape[1] * 2, input_layer.shape[2] * 2), method='nearest')


def yoloV3(input_layer, num_classes):
    route_1, route_2, conv = darknet_53(input_layer)

    conv = convolutional(conv, (1, 1, 1024, 512))
    conv = convolutional(conv, (3, 3, 512, 1024))
    conv = convolutional(conv, (1, 1, 1024, 512))
    conv = convolutional(conv, (3, 3, 512, 1024))
    conv = convolutional(conv, (1, 1, 1024, 512))

    # For Large(13X13) boxes
    conv_lobj_branch = convolutional(conv, (3, 3, 512, 1024))
    conv_lbbox = convolutional(conv_lobj_branch, (1, 1, 1024, 3 * (num_classes + 5)), activate=False, batch_norm=False)

    conv = convolutional(conv, (1, 1, 512, 256))
    conv = upsample(conv)

    conv = tf.concat([conv, route_2], axis=-1)
    conv = convolutional(conv, (1, 1, 768, 256))
    conv = convolutional(conv, (3, 3, 256, 512))
    conv = convolutional(conv, (1, 1, 512, 256))
    conv = convolutional(conv, (3, 3, 256, 512))
    conv = convolutional(conv, (1, 1, 512, 256))

    # For Medium(26X26) boxes
    conv_mobj_branch = convolutional(conv, (3, 3, 256, 512))
    conv_mbbox = convolutional(conv_mobj_branch, (1, 1, 512, 3 * (num_classes + 5)),
                               activate=False, batch_norm=False)

    conv = convolutional(conv, (1, 1, 256, 128))
    conv = upsample(conv)

    conv = tf.concat([conv, route_1], axis=-1)

    conv = convolutional(conv, (1, 1, 384, 128))
    conv = convolutional(conv, (3, 3, 128, 256))
    conv = convolutional(conv, (1, 1, 256, 128))
    conv = convolutional(conv, (3, 3, 128, 256))
    conv = convolutional(conv, (1, 1, 256, 128))

    # For Small(52X52) boxes
    conv_sobj_branch = convolutional(conv, (3, 3, 128, 256))
    conv_sbbox = convolutional(conv_sobj_branch,
                               (1, 1, 256, 3 * (num_classes + 5)), activate=False, batch_norm=False)

    return [conv_sbbox, conv_mbbox, conv_lbbox]


def decode(conv_out, i, anchors, stride, num_classes):
    conv_shape = tf.shape(conv_out)
    batch_size = conv_shape[0]
    output_size = conv_shape[1]

    conv_output = tf.reshape(conv_out, (batch_size, output_size, output_size, 3, 5 + num_classes))

    conv_raw_dxdy = conv_output[:, :, :, :, 0:2]
    conv_raw_dwdh = conv_output[:, :, :, :, 2:4]
    conv_raw_conf = conv_output[:, :, :, :, 4:5]
    conv_raw_prob = conv_output[:, :, :, :, 5:]

    y = tf.tile(tf.range(output_size, dtype=tf.int32)[:, tf.newaxis], [1, output_size])
    x = tf.tile(tf.range(output_size, dtype=tf.int32)[tf.newaxis, :], [output_size, 1])

    xy_grid = tf.concat([x[:, :, tf.newaxis], y[:, :, tf.newaxis]], axis=-1)
    xy_grid = tf.tile(xy_grid[tf.newaxis, :, :, tf.newaxis, :], [batch_size, 1, 1, 3, 1])
    xy_grid = tf.cast(xy_grid, tf.float32)

    pred_xy = (tf.sigmoid(conv_raw_dxdy) + xy_grid) * stride[i]
    pred_wh = (tf.exp(conv_raw_dwdh) * anchors[i]) * stride[i]
    pred_xywh = tf.concat([pred_xy, pred_wh], axis=-1)

    pred_conf = tf.sigmoid(conv_raw_conf)
    pred_prob = tf.sigmoid(conv_raw_prob)

    return tf.concat([pred_xywh, pred_conf, pred_prob], axis=-1)


def v3_model(num_classes, anchors, stride):
    input_layer = tf.keras.layers.Input([416, 416, 3])
    feature_maps = yoloV3(input_layer, num_classes)

    bbox_tensors = []

    for i, fm in enumerate(feature_maps):
        bbox_tensor = decode(fm, i, anchors, stride, num_classes)
        bbox_tensors.append(bbox_tensor)

    yolo_v3_model = tf.keras.Model(input_layer, bbox_tensors)

    return yolo_v3_model
