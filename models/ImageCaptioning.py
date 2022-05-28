import pickle

import numpy as np
import tensorflow as tf
from keras.applications.inception_v3 import preprocess_input
from keras.utils.data_utils import get_file
import pandas as pd
import uuid

keras = tf.keras

tokenizer_path = './utils/tokenizer.pickle'

# encoder_link = "https://drive.google.com/uc?export=download&id=1-9ExPtBo_x2Tx0A9ftKm4W9dTx9BnClR"
# decoder_link = "https://drive.google.com/uc?export=download&id=1-0ij64tm_5z8MMo4EBlEnBjTrpycqiX0"

encoder_link = "https://drive.google.com/uc?export=download&id=1-WUDdKCeqTbiDWTQZNR6ZXds2kq_Nufr"
decoder_link = "https://drive.google.com/uc?export=download&id=1-VjDMjKj2ZhmTRKk2KmiGhT0T-CfTbfb"

# Determining constants
max_cap_len = 20  # Determines max length of captioning sentences
img_dimension = 299  # Determines the height and width of images
num_words = 10000  # Determines vocab size to tokenize and train on
encoding_size = 512  # Determines dimension of the encodings of images
LSTM_size = 512
batch_size = 128
n_epochs = 15
Buffer_size = 1000
validation_and_test_split = 0.2
test_to_val_split = 0.5
num_examples = None  # Determines number of overall read samples. If set to none all samples will be read as long as they don't exceed max_cap_len


def load_img(image):
    # image = cv2.resize(image, (img_dimension, img_dimension), interpolation=cv2.INTER_LANCZOS4)
    img = tf.image.resize(image, (img_dimension, img_dimension))
    return img


def prepare_env():
    df = pd.read_csv("data/encoded_images.csv")

    # Loading encoder
    incep = keras.applications.inception_v3.InceptionV3(input_shape=(img_dimension, img_dimension, 3),
                                                        include_top=False)
    incep.trainable = False

    encoder = keras.models.Sequential([
        keras.layers.Lambda(preprocess_input, input_shape=(img_dimension, img_dimension, 3),
                            name="preprocessing_layer"),
        incep,
        keras.layers.Dense(encoding_size, activation='relu', name="encoding_layer"),
        keras.layers.Reshape((8 * 8, encoding_size), name="reshape_layer")
    ], name="Encoder")

    weights_path = get_file(
        'encoder_14_2.hdf5', encoder_link)
    encoder.load_weights(weights_path)

    # Loading decoder
    model_path = get_file(
        'decoder_14_2.h5', decoder_link)
    decoder = tf.keras.models.load_model(model_path)

    # Loading tokenizer
    with open(tokenizer_path, 'rb') as handle:
        tokenizer = pickle.load(handle)

    return encoder, decoder, tokenizer


def caption_image(encoder, decoder, tokenizer, image, image_time):
    image = load_img(image)  # /255.0
    encodings = encoder.predict(tf.reshape(image, (1, img_dimension, img_dimension, 3)))

    texts = ["<sos>"]
    h = np.zeros((1, LSTM_size))
    c = np.zeros((1, LSTM_size))

    for _ in range(max_cap_len + 1):
        dec_inp = np.array(tokenizer.word_index.get(texts[-1])).reshape(1, -1)

        props, h, c = decoder.predict([encodings, h, c, dec_inp])
        props = props[0]
        idx = np.argmax(props)

        texts.append(tokenizer.index_word.get(idx))

        if idx == tokenizer.word_index['<eos>']:
            break

    if tokenizer.word_index.get(texts[-1]) != tokenizer.word_index['<eos>']:
        texts.append('<eos>')

    result = ' '.join(texts[1:-1])

    return result


def caption_image_for_feedback(encoder, decoder, tokenizer, image, image_time):
    image = load_img(image)  # /255.0
    encodings = encoder.predict(tf.reshape(image, (1, img_dimension, img_dimension, 3)))

    texts = ["<sos>"]
    h = np.zeros((1, LSTM_size))
    c = np.zeros((1, LSTM_size))

    for _ in range(max_cap_len + 1):
        dec_inp = np.array(tokenizer.word_index.get(texts[-1])).reshape(1, -1)

        props, h, c = decoder.predict([encodings, h, c, dec_inp])
        props = props[0]
        idx = np.argmax(props)

        texts.append(tokenizer.index_word.get(idx))

        if idx == tokenizer.word_index['<eos>']:
            break

    if tokenizer.word_index.get(texts[-1]) != tokenizer.word_index['<eos>']:
        texts.append('<eos>')

    result = ' '.join(texts[1:-1])

    # Store input image for later improvement
    np_encoding_reshaped = np.array(encodings).reshape((1, -1))
    caption_id = uuid.uuid4()

    data = [[caption_id, image_time, np_encoding_reshaped.tolist(), result, "NaN", "NaN"]]
    data = pd.DataFrame(data, columns=["Id", "Date", "Encoded_Image", "Prediction", "Score", "Feedback"])

    data.to_csv("data/encoded_images.csv", mode="a", header=False, index=False)

    return caption_id, result
