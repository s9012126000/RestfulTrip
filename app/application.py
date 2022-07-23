from app.server import app
from waitress import serve


if __name__ == "__main__":
    if app.env == "production":
        serve(app, host="0.0.0.0", port=8080)
    else:
        app.run("0.0.0.0", port=8080)
