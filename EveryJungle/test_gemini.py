import google.generativeai as genai
from dotenv import load_dotenv

import os

load_dotenv() # .env 파일 열기

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-1.5-flash')

image_path = './static/portrait.jpg'
with open(image_path,'rb') as img_file:
    image_data = img_file.read()

response = model.generate_content([
    "사진에 나오는 오브젝트에 대한 상세한 묘사를 해줘",
    {"mime_type": "image/png", "data":image_data}
])
# response = model.generate_content("Write a story about magic island.")
print(response.text)