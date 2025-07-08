import time
import hmac
import hashlib
import base64
import requests
import logging

logger = logging.getLogger(__name__)

def make_zadarma_call(from_number, to_number):
    method = "v1/call/request/"
    base_url = "https://api.zadarma.com/"
    timestamp = int(time.time())
    query_string = f"{method}{timestamp}"

    # Підпис для авторизації
    sign = hmac.new(
        ZADARMA_API_SECRET.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha1
    ).hexdigest()

    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{ZADARMA_API_KEY}:{sign}'.encode()).decode()}",
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json"
    }

    payload = {
        "number_from": from_number,
        "number_to": to_number,
        "caller_id": from_number,
        "record": 0,
        "auto_answer": 1
    }

    url = base_url + method
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        json_resp = response.json()
        logger.info(f"Zadarma call response: {json_resp}")
        return json_resp
    except Exception as e:
        logger.error(f"Помилка при дзвінку Zadarma: {e}")
        return {"error": str(e)}

# Задля роботи цього модуля треба імпортувати конфіги
from config import ZADARMA_API_KEY, ZADARMA_API_SECRET
