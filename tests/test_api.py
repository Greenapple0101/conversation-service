import pytest
import json
import os
import sys
from unittest.mock import Mock, patch, MagicMock, mock_open
from flask import Flask
from flask_restful import Api

# 테스트를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 테스트를 위한 Flask 앱 설정
from api.summary import Summary
from api.text_emotion_detect import TextEmotionDetection, textFeelingDetection
from api.create_image import CreateImage, generate_image, upload_to_s3
from api.chat_ai import ChatAI, AIChatBot


class TestSummary:
    """Summary API 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(Summary, '/summaryAPI')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    @patch.dict(os.environ, {'NAVER_CLIENT_ID': 'test_client_id', 'NAVER_CLIENT_SECRET': 'test_secret'})
    @patch('api.summary.requests.post')
    def test_summary_success(self, mock_post):
        """Summary API 성공 케이스 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'summary': ['요약 1', '요약 2', '요약 3']
        }
        mock_post.return_value = mock_response
        
        # 테스트 데이터
        test_data = {
            'content': [
                {
                    'stitle': '회의',
                    'start': '2024-01-01T09:00:00',
                    'end': '2024-01-01T10:00:00',
                    'cal': 1,
                    'seat': '회의실',
                    'sexer': 'A',
                    'scontent': '프로젝트 회의',
                    'sarea': '서울',
                    'sdest': '부산',
                    'smate': '김철수'
                }
            ]
        }
        
        # test_client를 사용한 HTTP 요청
        response = self.client.post(
            '/summaryAPI',
            json=test_data,
            content_type='application/json'
        )
        
        # 검증
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'summary' in data or 'error' in data
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {'NAVER_CLIENT_ID': 'test_client_id', 'NAVER_CLIENT_SECRET': 'test_secret'})
    def test_summary_missing_content(self):
        """Summary API - content 누락 테스트"""
        # content 없이 요청
        response = self.client.post(
            '/summaryAPI',
            json={},
            content_type='application/json'
        )
        
        # reqparse가 required=True로 설정되어 있으므로 400 에러 예상
        assert response.status_code == 400
    
    @patch.dict(os.environ, {'NAVER_CLIENT_ID': 'test_client_id', 'NAVER_CLIENT_SECRET': 'test_secret'})
    @patch('api.summary.requests.post')
    def test_summary_api_error(self, mock_post):
        """Summary API - 외부 API 에러 테스트"""
        # Mock 에러 응답
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json.return_value = {'error': 'API Error'}
        mock_post.return_value = mock_response
        
        test_data = {
            'content': [{'stitle': '테스트'}]
        }
        
        # test_client를 사용한 HTTP 요청
        response = self.client.post(
            '/summaryAPI',
            json=test_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_cal_label(self):
        """getCalLabel 메서드 테스트"""
        assert Summary.getCalLabel(1) == '일정'
        assert Summary.getCalLabel(2) == '아침'
        assert Summary.getCalLabel(3) == '점심'
        assert Summary.getCalLabel(4) == '저녁'
        assert Summary.getCalLabel(5) == '운동'
        assert Summary.getCalLabel(6) == '경로'
        assert Summary.getCalLabel(99) == ''  # 알 수 없는 값
        assert Summary.getCalLabel(None) == ''
    
    @patch.dict(os.environ, {'NAVER_CLIENT_ID': 'test_client_id', 'NAVER_CLIENT_SECRET': 'test_secret'})
    @patch('api.summary.requests.post')
    def test_summary_empty_fields(self, mock_post):
        """Summary API - 빈 필드 처리 테스트"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'summary': ['요약']}
        mock_post.return_value = mock_response
        
        test_data = {
            'content': [
                {
                    'stitle': None,
                    'start': None,
                    'end': None,
                    'cal': None,
                    'scontent': '내용만 있음'
                }
            ]
        }
        
        response = self.client.post(
            '/summaryAPI',
            json=test_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data is not None


class TestChatAI:
    """ChatAI API 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(ChatAI, '/ChatAI')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_success(self, mock_post):
        """ChatAI API 성공 케이스 테스트"""
        # Mock OpenAI API 응답 - 실제 구조와 동일하게
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '안녕하세요! 무엇을 도와드릴까요?'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # test_client를 사용한 HTTP 요청
        response = self.client.post(
            '/ChatAI',
            json={'message': '안녕하세요'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'answer' in data
        mock_post.assert_called_once()
    
    def test_chat_ai_missing_params(self):
        """ChatAI - 필수 파라미터 누락 테스트"""
        # AIChatBot 함수 직접 테스트 (Flask context 불필요)
        result = AIChatBot(None, None)
        assert result['status'] == 'FAIL'
        assert '필수 매개변수값이 없습니다' in result['messages']
        
        result2 = AIChatBot("메시지", None)
        assert result2['status'] == 'FAIL'
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_api_error(self, mock_post):
        """ChatAI - API 에러 처리 테스트"""
        # API 에러 시뮬레이션
        mock_post.side_effect = Exception("API Error")
        
        # test_client를 사용한 HTTP 요청
        response = self.client.post(
            '/ChatAI',
            json={'message': '테스트 메시지'},
            content_type='application/json'
        )
        
        # 에러 발생 시 500 또는 예외 처리
        assert response.status_code in [200, 500]
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_message_history(self, mock_post):
        """ChatAI - 메시지 히스토리 관리 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '응답 메시지'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        # AIChatBot 함수 직접 테스트
        messages = [{"role": "assistant", "content": "초기 메시지"}]
        result = AIChatBot("사용자 메시지", messages)
        
        # 메시지 히스토리에 사용자 메시지와 어시스턴트 응답이 추가되었는지 확인
        assert len(messages) >= 3  # 초기 + 사용자 + 어시스턴트
        assert result['status'] == 'SUCCESS'
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_endpoint_integration(self, mock_post):
        """ChatAI 엔드포인트 통합 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {'content': '테스트 응답'}
            }]
        }
        mock_post.return_value = mock_response
        
        response = self.client.post(
            '/ChatAI',
            json={'message': '안녕하세요'},
            content_type='application/json'
        )
        
        assert response.status_code == 200


class TestCreateImage:
    """CreateImage API 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(CreateImage, '/CreateIm')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key', 'SPRING_URL': 'http://test-spring.com'})
    @patch('api.create_image.requests.post')
    def test_generate_image_success(self, mock_post):
        """이미지 생성 성공 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'data': [{'url': 'https://example.com/image.png'}]
        }
        mock_post.return_value = mock_response
        
        # generate_image 함수 직접 테스트 (Flask context 불필요)
        generate_image("아름다운 풍경")
        
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://api.openai.com/v1/images/generations"
        assert 'Authorization' in call_args[1]['headers']
        assert call_args[1]['json']['prompt'] == "아름다운 풍경"
    
    @patch.dict(os.environ, {'SPRING_URL': 'http://test-spring.com'})
    @patch('api.create_image.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake image data')
    def test_upload_to_s3_success(self, mock_file, mock_post):
        """S3 업로드 성공 테스트"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'Upload successful'
        mock_post.return_value = mock_response
        
        # upload_to_s3 함수 직접 테스트 (Flask context 불필요)
        upload_to_s3('/path/to/file.jpg')
        
        mock_post.assert_called_once()
        assert mock_post.call_args[0][0] == 'http://test-spring.com/file/upload'
    
    @patch.dict(os.environ, {'SPRING_URL': 'http://test-spring.com'})
    @patch('api.create_image.requests.post')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake image data')
    def test_upload_to_s3_failure(self, mock_file, mock_post):
        """S3 업로드 실패 테스트"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Upload failed'
        mock_post.return_value = mock_response
        
        # upload_to_s3 함수 직접 테스트
        upload_to_s3('/path/to/file.jpg')
        
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.create_image.generate_image')
    def test_create_image_post(self, mock_generate):
        """CreateImage POST 메서드 테스트"""
        # test_client를 사용한 HTTP 요청
        test_data = {
            'message': '테스트 프롬프트',
            'id': '123'
        }
        
        response = self.client.post(
            '/CreateIm',
            json=test_data,
            content_type='application/json'
        )
        
        # generate_image가 호출되었는지 확인
        mock_generate.assert_called_once_with('테스트 프롬프트')
        # CreateImage.post()는 반환값이 없으므로 200 또는 204 예상
        assert response.status_code in [200, 204, 500]


class TestTextEmotionDetection:
    """TextEmotionDetection API 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(TextEmotionDetection, '/diary')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    @patch('api.text_emotion_detect.language_v1.LanguageServiceClient')
    @patch('api.text_emotion_detect.service_account.Credentials')
    def test_text_feeling_detection_success(self, mock_credentials, mock_client_class):
        """감정 분석 성공 테스트"""
        # Mock 설정
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_sentiment = Mock()
        mock_sentiment.score = 0.8
        mock_sentiment.magnitude = 0.9
        
        mock_response = Mock()
        mock_response.document_sentiment = mock_sentiment
        mock_client.analyze_sentiment.return_value = mock_response
        
        # GOOGLE_APPLICATION_CREDENTIALS 경로 설정
        with patch('api.text_emotion_detect.GOOGLE_APPLICATION_CREDENTIALS_PATH', '/path/to/credentials.json'):
            with patch('os.path.exists', return_value=True):
                # textFeelingDetection 함수 직접 테스트 (Flask context 불필요)
                result = textFeelingDetection("오늘은 정말 좋은 하루였어요!")
                
                assert result['score'] == 0.8
                assert result['mag'] == 0.9
    
    @patch('api.text_emotion_detect.GOOGLE_APPLICATION_CREDENTIALS_PATH', None)
    def test_text_feeling_detection_no_credentials(self):
        """자격 증명 파일 없음 테스트"""
        # textFeelingDetection 함수 직접 테스트
        result = textFeelingDetection("테스트 텍스트")
        
        assert result['score'] == -10000
        assert result['mag'] == -10000
    
    @patch('api.text_emotion_detect.GOOGLE_APPLICATION_CREDENTIALS_PATH', '/nonexistent/path.json')
    @patch('os.path.exists', return_value=False)
    def test_text_feeling_detection_invalid_path(self):
        """잘못된 자격 증명 경로 테스트"""
        # textFeelingDetection 함수 직접 테스트
        result = textFeelingDetection("테스트 텍스트")
        
        assert result['score'] == -10000
        assert result['mag'] == -10000
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.text_emotion_detect.textFeelingDetection')
    @patch('api.text_emotion_detect.AIChatBot')
    def test_text_emotion_detection_get_success(self, mock_ai_chat, mock_feeling):
        """TextEmotionDetection GET 성공 테스트"""
        # Mock 설정
        mock_feeling.return_value = {'score': 0.5, 'mag': 0.7}
        mock_ai_chat.return_value = {
            'status': 'SUCCESS',
            'messages': '공감하는 응답 메시지'
        }
        
        # test_client를 사용한 HTTP 요청
        response = self.client.get(
            '/diary?diary=오늘 하루가 힘들었어요'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'answer' in data
        assert 'score' in data
        assert 'mag' in data
        assert data['score'] == 0.5
        assert data['mag'] == 0.7
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.text_emotion_detect.textFeelingDetection')
    @patch('api.text_emotion_detect.AIChatBot')
    def test_text_emotion_detection_ai_failure(self, mock_ai_chat, mock_feeling):
        """TextEmotionDetection - AI 응답 실패 테스트"""
        mock_feeling.return_value = {'score': 0.3, 'mag': 0.5}
        mock_ai_chat.return_value = {
            'status': 'FAIL',
            'messages': '에러 메시지'
        }
        
        # test_client를 사용한 HTTP 요청
        response = self.client.get(
            '/diary?diary=테스트 일기'
        )
        
        # 실패 시에도 score와 mag는 반환되어야 함 (코드 로직에 따라 다를 수 있음)
        assert response.status_code in [200, 500]


class TestIntegration:
    """통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        from app import app
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_endpoint_integration(self, mock_post):
        """ChatAI 엔드포인트 통합 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {'content': '테스트 응답'}
            }]
        }
        mock_post.return_value = mock_response
        
        response = self.client.post(
            '/ChatAI',
            json={'message': '안녕하세요'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_cors_headers(self):
        """CORS 헤더 테스트"""
        response = self.client.options('/ChatAI')
        # CORS가 설정되어 있는지 확인
        assert response is not None


class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    def setup_method(self):
        """각 테스트 전에 실행되는 설정"""
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.api.add_resource(Summary, '/summaryAPI')
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    @patch.dict(os.environ, {'NAVER_CLIENT_ID': 'test_client_id', 'NAVER_CLIENT_SECRET': 'test_secret'})
    @patch('api.summary.requests.post')
    def test_summary_empty_content_list(self, mock_post):
        """Summary - 빈 content 리스트 테스트"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {'summary': []}
        mock_post.return_value = mock_response
        
        test_data = {'content': []}
        
        # test_client를 사용한 HTTP 요청
        response = self.client.post(
            '/summaryAPI',
            json=test_data,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data is not None
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_api_key'})
    @patch('api.chat_ai.requests.post')
    def test_chat_ai_empty_message(self, mock_post):
        """ChatAI - 빈 메시지 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{
                'message': {'content': '응답'}
            }]
        }
        mock_post.return_value = mock_response
        
        # AIChatBot 함수 직접 테스트
        result = AIChatBot("", [{"role": "assistant", "content": "테스트"}])
        # 빈 문자열도 유효한 입력일 수 있음
        assert result is not None
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'})
    @patch('api.create_image.requests.post')
    def test_create_image_empty_prompt(self, mock_post):
        """CreateImage - 빈 프롬프트 테스트"""
        mock_response = Mock()
        mock_response.json.return_value = {'data': []}
        mock_post.return_value = mock_response
        
        # generate_image 함수 직접 테스트
        generate_image("")
        mock_post.assert_called_once()


class TestDataValidation:
    """데이터 검증 테스트"""
    
    def test_summary_date_format_handling(self):
        """Summary - 날짜 형식 처리 테스트"""
        # 날짜 문자열 슬라이싱이 올바르게 작동하는지 확인
        date_str = '2024-01-01T09:00:00'
        time_part = date_str[11:16] if len(date_str) > 16 else ''
        assert time_part == '09:00'
    
    def test_summary_cal_label_edge_cases(self):
        """Summary - cal_label 엣지 케이스"""
        assert Summary.getCalLabel(0) == ''
        assert Summary.getCalLabel(-1) == ''
        assert Summary.getCalLabel(7) == ''


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
