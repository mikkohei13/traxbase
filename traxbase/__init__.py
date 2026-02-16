from flask import Flask


def create_app():
    app = Flask(__name__)

    from traxbase.routes import main

    app.register_blueprint(main)

    return app
