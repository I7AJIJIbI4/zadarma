import os
from dotenv import load_dotenv

load_dotenv()

ZADARMA_API_KEY = os.getenv("ZADARMA_API_KEY")
ZADARMA_API_SECRET = os.getenv("ZADARMA_API_SECRET")
ZADARMA_FROM = os.getenv("ZADARMA_FROM")
ZADARMA_SIP = os.getenv("ZADARMA_SIP")

DTMF_TO_ROUTE = {
    "1": {"number": "0933297777"},
    "2": {"number": "0996093860"}
}
