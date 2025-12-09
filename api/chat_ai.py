import os
from flask_restful import Resource
from flask import request
from dotenv import load_dotenv
import requests

load_dotenv(override=False)

class ChatAI(Resource):
    def post(self):
        try:
            messages = [{"role": "assistant", "content": '''
                    You are Helthy-Real's customer service referral bot.
                    What we offer is a service PlayStation that provides personal digital maintenance services.
                    It can cut into your personal health and recommend only healthy exercises as well as recipes and assets.
                    We try to obtain health information in a way that is neutral to the individual.
                    When responding, be courteous and polite to all users.
                    If you have any questions that do not provide a clear answer, please reply 'Please contact the administrator.'
                    Please reply using access since you are a Korean bot and most of your users are the newest
                    If the user wishes to cancel payment or reservation, they will be contacted by a counselor at 010-1234-1234.
                    Please indicate the link https://health.kdca.go.kr/healthinfo/ for additional health information.
                    All answers must be provided in Korean.
                    '''}]
            args = request.get_json() or {}
            content = args.get('message', '')
            response = AIChatBot(content, messages)
            
            if response['status'] == 'SUCCESS':
                answer = response['messages']
                return {"answer": answer}, 200
            else:
                return {"status": "FAIL", "answer": response.get('messages', 'Unknown error')}, 500
        except Exception as e:
            return {"status": "FAIL", "answer": str(e)}, 500


def AIChatBot(content, message):
    print(f"ai 챗봇 api 키 값: {os.getenv('OPENAI_API_KEY')}")
    if content == None or message == None:
        return {'status': 'FAIL', 'messages': "필수 매개변수값이 없습니다"}
    try:
        message.append({'role':'user','content':content})
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4o-mini",
            "messages": message
        }
        response = requests.post(url, headers=headers, json=data)
        answer = response.json()["choices"][0]['message']['content']
        message.append({'role': 'assistant', 'content': answer})
        return {'status': 'SUCCESS', 'messages': answer}
    except Exception as e:
        return {'status': 'FAIL', 'messages': f"API Error: {e}"}