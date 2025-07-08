from zadarma_api import ZadarmaAPI
from config import ZADARMA_API_KEY, ZADARMA_API_SECRET

def test_auth():
    api = ZadarmaAPI(ZADARMA_API_KEY, ZADARMA_API_SECRET)
    response = api.call('/v1/numbers/')
    print('Response from /v1/numbers/:', response)

if __name__ == "__main__":
    test_auth()
