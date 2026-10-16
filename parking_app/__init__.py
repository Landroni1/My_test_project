from flask import Flask

from .models import db


def create_app(config_object=None):
    app = Flask(__name__)

    # Базовая конфигурация БД (при необходимости можно вынести в config.py)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config_object:
        app.config.from_object(config_object)

    db.init_app(app)

    from .routes import api_bp

    app.register_blueprint(api_bp)

    return app
