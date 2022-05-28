import socket
from io import BytesIO

import pandas as pd
import uvicorn
from fastapi import FastAPI, File, UploadFile

from models.ImageCaptioning import prepare_env, caption_image, caption_image_for_feedback
from models.ObjectDetection import *
from time import strftime, gmtime, time
import json
import csv
import sys

csv.field_size_limit(2147483647)

encoder = None
decoder = None
tokenizer = None
obj_detect_model = None

app = FastAPI()
image_time = None


def read_image_file(file) -> Image.Image:
    image = Image.open(BytesIO(file))
    return image


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/predict/image")
async def predict_api(file: UploadFile = File(...)):
    global image_time

    extension = file.filename.split(".")[-1] in ("jpg", "jpeg", "png")

    if not extension:
        return "Image must be jpg or png format!"

    image_time = strftime("%Y_%m_%d_%H_%M_%S", gmtime())
    image = read_image_file(await file.read())
    image = image.convert('RGB')
    image = np.array(image)

    start_time = time()
    objects = predict_img(obj_detect_model, image, image_time)

    prediction = objects + caption_image(encoder, decoder, tokenizer, image, image_time)

    travel_time = time() - start_time
    print(travel_time)
    print(prediction)
    print("-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*")

    return prediction


@app.post("/feed/image")
async def predict_api(file: UploadFile = File(...)):
    global image_time

    extension = file.filename.split(".")[-1] in ("jpg", "jpeg", "png")

    if not extension:
        return "Image must be jpg or png format!"

    image_time = strftime("%Y_%m_%d_%H_%M_%S", gmtime())
    image = read_image_file(await file.read())
    image = image.convert('RGB')
    image = np.array(image)

    start_time = time()
    objects = predict_img(obj_detect_model, image, image_time)

    caption_id, caption_result = caption_image_for_feedback(encoder, decoder, tokenizer, image, image_time)

    prediction = objects + caption_result

    travel_time = time() - start_time
    print(travel_time)
    print(prediction)
    print("-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*")

    result = json.dumps({'id': str(caption_id), 'result': prediction})
    result = result.replace('"', "")
    return result


@app.post("/feed")
def predict_api(caption_id: str, score: str, feedback: str):
    reader = csv.reader(open("data/encoded_images.csv"))
    lines = np.array(list(reader))
    row = np.where(lines[:, 0] == caption_id)[0][0]
    lines[row][4] = score
    lines[row][5] = feedback

    writer = csv.writer(open('data/encoded_images.csv', 'w'), lineterminator='\n')
    writer.writerows(lines.tolist())

    return "Thank you for your review"


if __name__ == '__main__':
    # df = pd.DataFrame(columns=["Id", "Date", "Encoded_Image", "Prediction", "Score", "Feedback"])
    # df.to_csv('encoded_images.csv', mode='a')

    encoder, decoder, tokenizer = prepare_env()
    obj_detect_model = prepare_model()
    print(obj_detect_model.summary())

    local_ip = [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]

    uvicorn.run(app, port=8080, host=local_ip)
