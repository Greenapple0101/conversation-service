# api/ai_client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=False)

def AIChatBot(content, message):
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"ai 챗봇 api 키 값: {api_key}")
    if not content or not message:
        return {'status': 'FAIL', 'messages': "필수 매개변수값이 없습니다"}

    try:
        message.append({'role': 'user', 'content': content})
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": message
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        answer = response.json()["choices"][0]['message']['content']
        return {'status': 'SUCCESS', 'messages': answer}
    except Exception as e:
        return {'status': 'FAIL', 'messages': f"API Error: {e}"}
