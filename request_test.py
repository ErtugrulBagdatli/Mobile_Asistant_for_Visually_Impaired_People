import requests
from gtts import gTTS
from playsound import playsound
import os
from tkinter import *
from tkinter import filedialog

# Choose file with file selection pop-up window
root = Tk()
root.withdraw()

root.filename = filedialog.askopenfilename(initialdir="C:/Users/Resul/Desktop/Bitirme/Okul_Bitirme/COCO/data",
                                           title="Select file")
print(root.filename)

# Request is send with specified image file
url = 'http://192.168.43.10:8080/predict/image'
files = {'file': open(root.filename, 'rb')}
response = requests.post(url, files=files)
print(response.text)

# Returned text is converted a mp3 file, is spoken by gTTS, and is deleted
file_name = "output.mp3"
myobj = gTTS(text=response.text[1:-1], lang='en', slow=False)
myobj.save(file_name)
playsound(file_name)
os.remove(file_name)
