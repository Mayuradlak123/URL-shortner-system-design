from app import redis_client

CACHE_TTL = 3600 * 24 # 24 hours

def get_cached_url(short_code):
    if redis_client:
        return redis_client.get(f"url:{short_code}")
    return None

def set_cached_url(short_code, long_url):
    if redis_client:
        redis_client.set(f"url:{short_code}", long_url, ex=CACHE_TTL)

def get_cached_history(ip_address):
    if redis_client:
        # We could use a list or set here, but for simplicity let's just cache the whole result
        return redis_client.get(f"history:{ip_address}")
    return None

def set_cached_history(ip_address, history_json):
    if redis_client:
        redis_client.set(f"history:{ip_address}", history_json, ex=300) # 5 minutes
