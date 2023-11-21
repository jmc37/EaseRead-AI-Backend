import redis
import os

def create_redis_client():
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=os.getenv("REDIS_PORT"),
        password=os.getenv("REDIS_PASS")
    )
    return redis_client