from flask import Flask
from telebot import apihelper

from admin.views import admin_blueprint, admin, login
from bot.bot_manager import BotManager
from config import *
from models import db


def init_app():
    apihelper.proxy = PROXY
    app = Flask('bot2telega')
    app.config['MONGODB_DB'] = DB_NAME
    app.config['SECRET_KEY'] = '6dddcba7e23dddba127f47595f3f2553'
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    db.init_app(app)
    admin.init_app(app)
    login.init_app(app)
    app.config['FLASK_ADMIN_SWATCH'] = 'flatly'
    app.register_blueprint(admin_blueprint)
    return app


if __name__ == "__main__":
    app = init_app()
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        BotManager()
    app.run(host=HOST, port=PORT, threaded=True)
