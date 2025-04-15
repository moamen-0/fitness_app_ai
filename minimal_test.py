"""
Minimal Flask app to test App Engine deployment
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, App Engine! This test app is working.'

@app.route('/healthz')
def health():
    return 'OK'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
