# SnipURL - Modern URL Shortener

A high-performance URL shortener built with Flask, SQLite, and Redis, following the ByteByteGo system design.

## Features
- **Fast Shortening**: Uses Base62 encoding for compact URLs.
- **Redirection Caching**: Redis integration for sub-millisecond redirect lookups.
- **REST API**: programmatic URL shortening via `/api/v1/data/shorten`.
- **User History**: IP-based history tracking to see your recently shortened links.
- **Analytics Ready**: Uses 302 redirects for better click-through tracking.
- **Premium UI**: Modern, responsive design built with Tailwind CSS.

## Prerequisites
- Python 3.8+
- MongoDB Server (Local or Atlas)
- Redis Server (Optional, but recommended for caching)

## Setup and Installation

1. **Clone the repository** (or navigate to the folder):
   ```bash
   cd url-shortner-design
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**:
   Ensure MongoDB and Redis are running. Update the `MONGO_URI` in `.env` if necessary.

5. **Run the application**:
   ```bash
   python app.py
   ```

## Redirection Strategy & Data Retrieval

### 1. Why 302 Redirects?
The system implements **302 (Found)** redirects instead of 301 (Moved Permanently). 
- **Analytics & Tracking**: Since 302 redirects are temporary, the browser will always hit our server before going to the destination. This allows us to capture visit analytics, IP addresses, and user agents for history tracking.
- **Cache Control**: 301 redirects are cached aggressively by browsers, which would prevent us from tracking subsequent visits from the same user.

### 2. High-Speed Extraction Logic
To handle redirection at scale, the system follows this hierarchy:
1. **Redis Cache (L1)**: Immediate lookup using the `short_code`. If found, redirected instantly.
2. **MongoDB (L2)**: If cache misses, the system queries the `urls` collection using a unique index on `short_code`.
3. **Lazy Caching**: When a record is fetched from MongoDB, it is automatically written to Redis with a TTL to accelerate future requests.

## Folder Structure
- `app/`: Main application package
  - `routes.py`: Flask route handlers for UI, API, and Redirection.
  - `services/`: Specialized logic for Bloom Filter, Shortening, and Caching.
  - `templates/`: AJAX-enabled HTML templates using Tailwind CSS.
- `config.py`: Environment-aware configuration settings.
- `app.py`: Entry point for the application.
- `.env`: Secret keys and connection strings.
- `requirements.txt`: Project dependencies.
