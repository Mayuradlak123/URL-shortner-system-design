import hashlib
from app import redis_client

class BloomFilter:
    def __init__(self, redis_conn, key="url_bloom", size=10**7, hash_count=7):
        """
        Redis-based Bloom Filter.
        :param redis_conn: Redis connection object
        :param key: Redis key for the bitset
        :param size: Number of bits (m)
        :param hash_count: Number of hash functions (k)
        """
        self.redis = redis_conn
        self.key = key
        self.size = size
        self.hash_count = hash_count

    def _hashes(self, item):
        """
        Generates k hash values for an item.
        """
        hashes = []
        for i in range(self.hash_count):
            # Using MD5 and a salt to generate multiple hashes
            hash_val = int(hashlib.md5((item + str(i)).encode()).hexdigest(), 16)
            hashes.append(hash_val % self.size)
        return hashes

    def add(self, item):
        """
        Adds an item to the Bloom Filter.
        """
        if not self.redis:
            return
        pipeline = self.redis.pipeline()
        for pos in self._hashes(item):
            pipeline.setbit(self.key, pos, 1)
        pipeline.execute()

    def contains(self, item):
        """
        Checks if an item probably exists in the Bloom Filter.
        """
        if not self.redis:
            return False
        for pos in self._hashes(item):
            if not self.redis.getbit(self.key, pos):
                return False
        return True

    def clear(self):
        """
        Clears the Bloom Filter bitset.
        """
        if self.redis:
            self.redis.delete(self.key)
