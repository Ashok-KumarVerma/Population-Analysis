from flask import app
from flask_cors import CORS


CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})
