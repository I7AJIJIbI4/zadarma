# Zadarma Callback Tool

Приймає події з Zadarma та ініціює вихідні дзвінки на основі вибору DTMF.

## Встановлення

```bash
git clone ...
cd zadarma-callback-tool
python -m venv venv
source venv/bin/activate  # або venv\Scripts\activate на Windows
pip install -r requirements.txt
```

## Налаштування

Створіть файл `.env` і вкажіть ваші облікові дані Zadarma:

```
ZADARMA_API_KEY=...
ZADARMA_API_SECRET=...
ZADARMA_FROM=+380733103110
ZADARMA_SIP=107122
```

## Запуск

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```
