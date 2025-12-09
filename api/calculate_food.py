import ast
import json
import os
from flask import jsonify
from flask_restful import Resource
from flask import request
from dotenv import load_dotenv
import requests
from api.ai_client import AIChatBot

load_dotenv(override=False)

class CalculateCalo(Resource):
    def post(self):
        message = [{"role": "assistant", "content": '''
                너는 음식의 칼로리 계산기야. 
                사용자가 아래의 형식으로 데이터를 보내면 1인분 기준의 calorie, carbohydrate, protein, fat, sodium, cholesterol 수치를 계산해줘.

                사용자가 보내는 형식의 예시는 다음과 같아.
                만약 [재료] 관련 데이터가 없다면 [음식 이름]만 고려해서 값을 추정해줘.
                `
                [음식 이름]
                닭가슴살 부추냉채무침
                
                [재료]
                닭가슴살,300g 고구마 작은 것,4개 대파,1개 간장,3숟가락 다진 마늘,1숟가락 후추,약간 설탕,1/2숟가락 올리고당,1숟가락 미림,2숟가락 참기름,약간 검은깨,약간
                `
                네가 생성해야 하는 답변의 형식 예시는 다음과 같아.
                '{"calorie": 200, "carbohydrate": 44.5, "protein": 66.5, "fat": 29.5, "sodium": 805, "cholesterol": 100 }'
                '''}]
        name = request.json['name']
        ingredient = request.json['ingredient']
        content = f"""
        [음식 이름]
        {name}
        
        [재료]
        {ingredient}
        """
        response = AIChatBot(content, message)
        message = response['messages']
        if response['status'] == 'SUCCESS':
            answer = response['messages']
            print(f'반환 {answer}')
            try:
                data = json.loads(answer)
                return data, 200
            except:
                data = ast.literal_eval(answer)
                return data, 200
        else:
            print(f'오류 발생: {message}')