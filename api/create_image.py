import os
import requests
from dotenv import load_dotenv
from flask_restful import Resource
from flask import request

load_dotenv()

def upload_to_s3(file_path):
    requestUrl = f"{os.getenv('SPRING_URL')}/file/upload"
    print("요청 url 체크: ", requestUrl)
    with open(file_path, "rb") as f:
        files = {"file":f}
        response = requests.post(requestUrl, files=files)
    if response.status_code == 200:
        print("업로드 성공:", response.text)
    else:
        print("업로드 실패:", response.status_code, response.text)

def generate_image(prompt):
    url = "https://api.openai.com/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-image-1",
        "prompt": prompt,
        "size": "1024x1024"
    }
    response = requests.post(url, headers=headers, json=data)
    print("사진 생성 결과: ", response.json())

class CreateImage(Resource):
    def post(self):
        prompt = request.json['message']
        id = request.json['id']
        generate_image(prompt)