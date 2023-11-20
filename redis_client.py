import redis
import os

def create_redis_client():
    redis_client = redis.Redis(
        host=os.getenv("REDIS-HOST"),
        port=os.getenv("REDIS-PORT"),
        password=os.getenv("REDIS-PASS")
    )
