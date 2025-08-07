import requests
import logging
from config import WLAUNCH_API_URL, WLAUNCH_COMPANY_ID, WLAUNCH_API_BEARER
from users_db import add_or_update_client

logger = logging.getLogger("wlaunch_api")

HEADERS = {
    "Authorization": WLAUNCH_API_BEARER,
    "Accept": "application/json"
}

def fetch_all_clients():
    page = 0
    size = 100
    total_pages = 1
    while page < total_pages:
        url = f"{WLAUNCH_API_URL}/company/{WLAUNCH_COMPANY_ID}/client"
        params = {
            "page": page,
            "size": size,
            "sort": "created,desc"
        }
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            total_pages = data.get("page", {}).get("total_pages", 1)
            for client in data.get("content", []):
                add_or_update_client(
                    client_id=client.get("id"),
                    first_name=client.get("first_name") or "",
                    last_name=client.get("last_name") or "",
                    phone=client.get("phone") or ""
                )
            page += 1
        except Exception as e:
            logger.error(f"Помилка завантаження клієнтів: {e}")
            break
