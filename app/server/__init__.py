from werkzeug.exceptions import HTTPException
from flask import Flask
from dotenv import load_dotenv
import os
load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['JSON_AS_ASCII'] = False


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    return "Internal server Error", 500


from app.server.controllers import hotels_controller, dashboard_controller