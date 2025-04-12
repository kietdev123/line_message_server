import os
import requests
import hmac
import hashlib
import base64
from dotenv import load_dotenv

load_dotenv()

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
BASE_URL = os.getenv("BASE_URL")

class LineService:
    @staticmethod
    def verify_signature(body: bytes, signature: str) -> bool:
        if not LINE_CHANNEL_SECRET:
            return False
        hash = hmac.new(
            LINE_CHANNEL_SECRET.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        return signature == base64.b64encode(hash).decode('utf-8')

    @staticmethod
    def get_link_token(user_id: str) -> str:
        url = f"https://api.line.me/v2/bot/user/{user_id}/linkToken"
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["linkToken"]

    @staticmethod
    def send_message(user_id: str, message: str) -> bool:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "to": user_id,
            "messages": [{"type": "text", "text": message}]
        }
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200

    @staticmethod
    def create_link_url(link_token: str, nonce: str) -> str:
        return f"https://access.line.me/dialog/bot/accountLink?linkToken={link_token}&nonce={nonce}" 