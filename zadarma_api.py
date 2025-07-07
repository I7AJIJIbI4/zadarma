from zadarma_api import Zadarma
from config import ZADARMA_API_KEY, ZADARMA_API_SECRET, ZADARMA_SIP

zd = Zadarma(key=ZADARMA_API_KEY, secret=ZADARMA_API_SECRET)

async def make_callback(from_number: str, to_number: str):
    from asyncio.to_thread import to_thread

    def _make_request():
        return zd.request(
            method="/v1/request/callback/",
            params={
                "from": from_number,
                "to": to_number,
                "sip": ZADARMA_SIP
            }
        )

    return await to_thread(_make_request)
