from flask_restful import Resource, reqparse
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv(override=False)

class Summary(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('content', type=list, required=True,
                                   help='No content provided', location='json')
        self.client_id=os.getenv('NAVER_CLIENT_ID')
        self.client_secret=os.getenv('NAVER_CLIENT_SECRET')

        self.headers = {
            'Accept': 'application/json;UTF-8',
            'Content-Type': 'application/json;UTF-8',
            'X-NCP-APIGW-API-KEY-ID': self.client_id,
            'X-NCP-APIGW-API-KEY': self.client_secret
        }
        self.url = 'https://naveropenapi.apigw.ntruss.com/text-summary/v1/summarize'
        super(Summary, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        combined_content = []
        for item in args['content']:
            cal_label = self.getCalLabel(item.get('cal')) if item.get('cal') is not None else ''
            seat = item.get('seat', '') if item.get('seat') is not None else ''
            sexer = item.get('sexer', '') if item.get('sexer') is not None else ''
            seat_sexer_info = ''.join([seat, sexer]) if seat or sexer else ''
            cal_info_str = f"{cal_label}은 {seat_sexer_info}입니다." if cal_label and seat_sexer_info else ''
            content_parts = [
                f"{item.get('stitle', '')}는" if item.get('stitle') else '',
                f"{item.get('start', '')[11:16]}부터" if item.get('start') else '',
                f"{item.get('end', '')[11:16]}까지 입니다." if item.get('end') else '',
                cal_info_str,
                item.get('scontent', '') if item.get('scontent') else '',
                f"{item.get('sarea', '')}에서 출발하며, " if item.get('sarea') else '',
                f"{item.get('sdest', '')}에 도착합니다." if item.get('sdest') else '',
                f"같이 가는 메이트는 {item.get('smate', '')}입니다." if item.get('smate') else ''
            ]
            content_str = ' '.join(part for part in content_parts if part)
            combined_content.append(content_str)
        # 모든 타임라인 합치기
        final_content = ' '.join(combined_content)

        data = {
            "document": {
                "content": final_content
            },
            "option": {
                "language": "ko",
                "model": "general",
                "tone": 2,
                "summaryCount": 3
            }
        }
        response = requests.post(self.url, headers=self.headers, data=json.dumps(data).encode('UTF-8'))
        summary = response.json() if response.ok else {'error': response.json()}
        return summary

    @staticmethod
    def getCalLabel(cal):
        switcher = {
            1: '일정',
            2: '아침',
            3: '점심',
            4: '저녁',
            5: '운동',
            6: '경로'
        }
        return switcher.get(cal, '')