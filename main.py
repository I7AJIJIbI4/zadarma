from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from config import DTMF_TO_ROUTE, ZADARMA_FROM
from zadarma_api import make_callback
import logging

app = FastAPI()
logging.basicConfig(level=logging.INFO)

@app.post("/zadarma-callback")
async def zadarma_callback(request: Request):
    form = await request.form()
    event = form.get("event")
    dtmf = form.get("dtmf")
    call_id = form.get("call_id")

    logging.info(f"Подія: {event}, DTMF: {dtmf}, Call ID: {call_id}")

    if event == "DTMF" and dtmf in DTMF_TO_ROUTE:
        route = DTMF_TO_ROUTE[dtmf]
        response = await make_callback(ZADARMA_FROM, route["number"])
        logging.info(f"Вихідний дзвінок на {route['number']}: {response}")
        return {"status": "initiated", "response": response}

    return {"status": "ignored"}
