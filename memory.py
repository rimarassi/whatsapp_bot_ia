import redis

from langchain_community.chat_message_histories import RedisChatMessageHistory

from config import REDIS_URL


def get_session_history(session_id):
    return RedisChatMessageHistory(
        session_id=session_id,
        url=REDIS_URL,
    )


_redis = redis.from_url(REDIS_URL)


def is_duplicate(message_id, ttl=300):
    """Marca a mensagem no Redis. Retorna True se ela já foi processada."""
    key = f'webhook:processed:{message_id}'
    return not _redis.set(key, '1', nx=True, ex=ttl)
