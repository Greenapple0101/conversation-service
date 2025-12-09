import ast
import json
import os
from flask import jsonify
from flask_restful import Resource
from flask import request
from dotenv import load_dotenv
import requests

load_dotenv(override=False)


class CalculateCalo(Resource):
    def post(self):
        try:
            print("요청 처리 시작")
            api_key = os.getenv("OPENAI_API_KEY")
            messages = [{"role": "assistant", "content": '''
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
            messages.append({'role': 'user', 'content': content})
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": messages
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            print(f"response json 형식: {response.json()}")
            answer = response.json()["choices"][0]['message']['content']
            return answer, 200
            # print(f'answer? :{str(answer)}')
            # print(f'반환 {answer}')
            # try:
            #     data = json.loads(answer)
            #     return data, 200
            # except Exception as e:
            #     data = ast.literal_eval(answer)
            #     return data, 200
        except Exception as e:
            print(f'오류 발생: {str(e)}')
            return {'error': str(e)}, 500