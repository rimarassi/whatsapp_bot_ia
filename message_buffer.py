import asyncio
import redis.asyncio as redis

from config import REDIS_URL, BUFFER_KEY_SUFIX, DEBOUNCE_SECONDS, BUFFER_TTL
from evolution_api import send_whatsapp_message
from chains import get_conversational_rag_chain


redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
conversational_rag_chain = get_conversational_rag_chain()
debounce_tasks = {}


def log(*args):
    print('[BUFFER]', *args)


async def buffer_message(chat_id: str, message: str):
    buffer_key = f'{chat_id}{BUFFER_KEY_SUFIX}'

    await redis_client.rpush(buffer_key, message)
    await redis_client.expire(buffer_key, BUFFER_TTL)

    log(f'Mensagem adicionada ao buffer de {chat_id}: {message}')

    if debounce_tasks.get(chat_id):
        debounce_tasks[chat_id].cancel()
        log(f'Debounce resetado para {chat_id}')

    debounce_tasks[chat_id] = asyncio.create_task(handle_debounce(chat_id))


async def handle_debounce(chat_id: str):
    buffer_key = f'{chat_id}{BUFFER_KEY_SUFIX}'
    limpar_buffer = True

    try:
        log(f'Iniciando debounce para {chat_id}')
        await asyncio.sleep(float(DEBOUNCE_SECONDS))

        messages = await redis_client.lrange(buffer_key, 0, -1)
        full_message = ' '.join(messages).strip()
        if not full_message:
            return

        log(f'Enviando mensagem agrupada para {chat_id}: {full_message}')

        ai_response = ''
        for tentativa in range(1, 4):
            try:
                resposta = await asyncio.to_thread(
                    conversational_rag_chain.invoke,
                    input={'input': full_message},
                    config={'configurable': {'session_id': chat_id}},
                )
                ai_response = resposta['answer'].strip()
                if ai_response:
                    break
                log(f'Resposta vazia na tentativa {tentativa}/3')
            except Exception as exc:
                log(f'Erro na cadeia {tentativa}/3: {type(exc).__name__}: {exc}')

        if not ai_response:
            ai_response = 'Desculpe, não consegui responder agora.'

        await asyncio.to_thread(
            send_whatsapp_message,
            number=chat_id,
            text=ai_response,
        )
        log(f'Resposta enviada para {chat_id}')

    except asyncio.CancelledError:
        limpar_buffer = False
        log(f'Debounce cancelado para {chat_id}')
    except Exception as exc:
        log(f'Erro ao processar {chat_id}: {type(exc).__name__}: {exc}')
    finally:
        if limpar_buffer:
            await redis_client.delete(buffer_key)
        if debounce_tasks.get(chat_id) is asyncio.current_task():
            debounce_tasks.pop(chat_id, None)
