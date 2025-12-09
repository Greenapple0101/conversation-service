import os
from flask import Flask, Response
from flask_restful import Api
from flask_cors import CORS
from api.summary import Summary
from api.text_emotion_detect import TextEmotionDetection
from api.create_image import CreateImage
from api.chat_ai import ChatAI
from api.calculate_food import CalculateCalo

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)

api.add_resource(Summary, '/summaryAPI')
api.add_resource(TextEmotionDetection, '/diary')
api.add_resource(CreateImage, "/CreateIm")
api.add_resource(ChatAI, "/ChatAI")
api.add_resource(CalculateCalo, "/calculate-calo")

@app.route('/health')
def health():
    return {"status": "ok", "service": "conversation-service"}, 200

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='127.0.0.1', port=5000)