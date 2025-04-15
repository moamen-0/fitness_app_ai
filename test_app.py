"""
Minimal test app to verify Cloud Run deployment
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({
        "status": "ok",
        "message": "Test app is running successfully",
        "service": "Fitness App"
    })

@app.route('/health')
def health():
    return "OK"

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# WSGI application
application = app
