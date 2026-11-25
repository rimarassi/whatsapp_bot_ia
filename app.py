from fastapi import FastAPI, Request

from message_buffer import buffer_message
from memory import is_duplicate


app = FastAPI()


@app.post('/webhook')
async def webhook(request: Request):
    payload = await request.json()

    if payload.get('event') != 'messages.upsert':
        return {'status': 'ignored'}

    data = payload.get('data') or {}
    key = data.get('key') or {}
    message = data.get('message') or {}

    chat_id = key.get('remoteJid')
    message_id = key.get('id')
    text = (
        message.get('conversation')
        or (message.get('extendedTextMessage') or {}).get('text')
    )

    if (
        key.get('fromMe')
        or not chat_id
        or not text
        or '@g.us' in chat_id
    ):
        return {'status': 'ignored'}

    if message_id and is_duplicate(message_id):
        return {'status': 'duplicate'}

    await buffer_message(chat_id=chat_id, message=text)

    return {'status': 'ok'}
