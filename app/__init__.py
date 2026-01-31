from flask import Flask
from config import Config
from pymongo import MongoClient
import redis

mongo_client = None
db = None
redis_client = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    global mongo_client, db, redis_client, bloom_filter
    
    # MongoDB Connection
    try:
        mongo_client = MongoClient(app.config['MONGO_URI'], serverSelectionTimeoutMS=2000)
        db = mongo_client.get_default_database()
        mongo_client.admin.command('ping')
        print(f"✅ Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

    # Redis Connection
    try:
        redis_client = redis.from_url(app.config['REDIS_URL'])
        redis_client.ping()
        print(f"✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    # Bloom Filter Initialization
    from app.services.bloom_service import BloomFilter
    bloom_filter = BloomFilter(redis_client)
    print("✅ Bloom Filter initialized (incremental seeding mode).")

    # MongoDB Indices
    if db is not None:
        db.urls.create_index("short_code", unique=True)
        print("✅ Unique index on 'short_code' verified.")

    from app import routes
    app.register_blueprint(routes.bp)

    return app
