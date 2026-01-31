from flask import Blueprint, render_template, request, redirect, jsonify
from app import db, redis_client, bloom_filter
from app.services.shortener_service import generate_short_code
from app.services.cache_service import get_cached_url, set_cached_url
from datetime import datetime

bp = Blueprint('main', __name__)

def get_client_ip():
    """
    Robustly extracts the client's IP address, handling proxies and local development.
    """
    if request.headers.get('X-Forwarded-For'):
        # Usually the first IP in the list is the original client
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # If not behind a proxy, use remote_addr
    ip = request.remote_addr
    
    # Optional: If you want to force a public IP check for local development, 
    # you could use an external service, but usually we stick to the request context.
    return ip or 'unknown'

@bp.route('/', methods=['GET'])
def index():
    user_ip = get_client_ip()
    return render_template('index.html', history=get_history(user_ip))

@bp.route('/shorten', methods=['POST'])
def shorten():
    long_url = request.form.get('long_url')
    if not long_url:
        return jsonify({"error": "URL is required"}), 400
    
    user_ip = get_client_ip()
    
    # Generate unique random short code with Bloom Filter optimized check
    max_attempts = 10
    short_code = None
    for _ in range(max_attempts):
        temp_code = generate_short_code()
        
        # 1. Check Bloom Filter (Fast, Probabilistic)
        if bloom_filter and bloom_filter.contains(temp_code):
            # Potential collision, verify with DB (Slower)
            if db.urls.find_one({'short_code': temp_code}):
                continue # Real collision
        
        # 2. No collision (either not in Bloom or False Positive verified by DB)
        short_code = temp_code
        break
    
    if not short_code:
        return jsonify({"error": "Failed to generate unique short code. Please try again."}), 500

    new_url = {
        'long_url': long_url,
        'short_code': short_code,
        'user_ip': user_ip,
        'created_at': datetime.utcnow()
    }
    db.urls.insert_one(new_url)
    
    # 3. Add to Bloom Filter for future collision checks
    if bloom_filter:
        bloom_filter.add(short_code)
    
    # Cache the new URL
    set_cached_url(short_code, long_url)
    
    short_url = request.host_url + short_code
    return jsonify({"short_url": short_url, "short_code": short_code, "long_url": long_url})

@bp.route('/api/v1/data/shorten', methods=['POST'])
def api_shorten():
    data = request.get_json()
    if not data or 'longUrl' not in data:
        return jsonify({"error": "longUrl is required"}), 400
    
    long_url = data['longUrl']
    user_ip = get_client_ip()
    
    # Generate unique short code with Bloom Filter
    short_code = None
    for _ in range(10):
        temp_code = generate_short_code()
        if bloom_filter and bloom_filter.contains(temp_code):
            if db.urls.find_one({'short_code': temp_code}):
                continue
        short_code = temp_code
        break
    
    if not short_code:
        return jsonify({"error": "Collision overflow"}), 500

    new_url = {
        'long_url': long_url,
        'short_code': short_code,
        'user_ip': user_ip,
        'created_at': datetime.utcnow()
    }
    db.urls.insert_one(new_url)
    
    if bloom_filter:
        bloom_filter.add(short_code)
        
    set_cached_url(short_code, long_url)
    
    return jsonify({"shortUrl": request.host_url + short_code}), 201

@bp.route('/<short_code>')
def redirect_to_long(short_code):
    # Try Cache first
    long_url = get_cached_url(short_code)
    if long_url:
        if isinstance(long_url, bytes):
            long_url = long_url.decode('utf-8')
        record_visit(short_code)
        return redirect(long_url, code=302)
    
    # Try DB
    url_record = db.urls.find_one({'short_code': short_code})
    if url_record:
        set_cached_url(short_code, url_record['long_url'])
        record_visit(short_code) 
        return redirect(url_record['long_url'], code=302)
    
    return "URL not found", 404

def get_history(ip_address):
    cursor = db.urls.find({'user_ip': ip_address}).sort('created_at', -1).limit(10)
    return list(cursor)

def record_visit(short_code):
    visit = {
        'short_code': short_code,
        'ip_address': get_client_ip(),
        'user_agent': request.user_agent.string,
        'visited_at': datetime.utcnow()
    }
    db.visits.insert_one(visit)
