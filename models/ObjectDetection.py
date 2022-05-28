from PIL import Image

from utils.Utils import *
from utils.YOLOV3 import *
from tensorflow.python.keras.utils.data_utils import get_file
import pandas as pd
import numpy as np

names = dict(pd.read_csv("./utils/class_names.csv").values)
yolo_model_link = "https://drive.google.com/uc?export=download&id=17oBrlSvutfgM98rVKcWW1eBFTxhn32gd&confirm=t"


def prepare_model():
    model_path = get_file('yolo.h5', yolo_model_link)
    return tf.keras.models.load_model(model_path)


def predict_img(model, img, image_time=""):
    img_in = tf.expand_dims(img, 0)
    img_in = transform_images(img_in, 416)
    pred_bbox = model.predict(img_in)

    pred_bbox = [tf.reshape(x, (-1, tf.shape(x)[-1])) for x in pred_bbox]

    pred_bbox = tf.concat(pred_bbox, axis=0)

    boxes, class_names, scores = box_detector(pred_bbox)

    # Saves image with detected objects
    # obj_detected_img = drawbox(boxes, class_names, scores, names, img)
    # im = Image.fromarray(obj_detected_img)
    # im.save(f'C:/Users/Resul/Desktop/Final_Year/outputs/output_{image_time}.jpg')

    # Eliminates fail detections
    data = np.concatenate([boxes, scores[:, np.newaxis], class_names[:, np.newaxis]], axis=-1)
    data = data[np.logical_and(data[:, 0] >= 0, data[:, 0] <= 416)]
    data = data[np.logical_and(data[:, 1] >= 0, data[:, 1] <= 416)]
    data = data[np.logical_and(data[:, 2] >= 0, data[:, 2] <= 416)]
    data = data[np.logical_and(data[:, 3] >= 0, data[:, 3] <= 416)]
    objects = data[data[:, 4] > 0.4]

    detected_objs_nums = {}
    name_singulars = list(names.keys())

    for object in objects:
        object_label_class = int(object[5])

        if name_singulars[object_label_class] in detected_objs_nums.keys():
            detected_objs_nums[name_singulars[object_label_class]] = detected_objs_nums[
                                                                         name_singulars[object_label_class]] + 1
        else:
            detected_objs_nums[name_singulars[object_label_class]] = 1

    singular_text = "There is "
    plural_text = "There are "

    for obj in detected_objs_nums.keys():
        if detected_objs_nums[obj] == 1:
            singular_text = singular_text + f"one {obj}, "
        else:
            plural_text = plural_text + f"{detected_objs_nums[obj]} {names[obj]}, "

    if len(singular_text) <= 9:
        singular_text = ''
    else:
        singular_text = singular_text[:len(singular_text) - 2] + ". "

    if len(plural_text) <= 10:
        plural_text = ''
    else:
        plural_text = plural_text[:len(plural_text) - 2] + ". "

    result_text = singular_text + plural_text

    return result_text

# import cv2
# model = prepare_model()
# img = cv2.imread(r"C:\Users\Resul\Desktop\Bitirme\Okul_Bitirme\COCO\data\000000000036.jpg")
# cv2.imshow("Test", predict_img(model, img))
# cv2.waitKey()
