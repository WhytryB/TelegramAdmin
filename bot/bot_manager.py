from threading import Thread

import telebot

from bot.bot_handlers import BotHandlers
from models import BotProfile


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class BotManager(metaclass=Singleton):
    _bots = dict()

    def __init__(self):
        active_bots = BotProfile.objects(active=True)
        for bot in active_bots:
            try:
                self.run(bot)
            except Exception as ex:
                bot.active = False
                BotProfile.save(bot)

    def get(self, bot_id):
        return self._bots.get(bot_id)

    def stop(self, bot_id):
        t_bot = self._bots.get(bot_id)
        if t_bot is not None:
            t_bot.stop_polling()
            del self._bots[bot_id]
            print(f"Stopped Bot#{0}", bot_id)

    def is_running(self, bot_id):
        return self._bots.get(bot_id) is not None

    def run(self, bot):
        t_bot = telebot.TeleBot(bot.token, threaded=False)
        t_bot.remove_webhook()
        Thread(name=f'Bot#{bot.id}-polling-thread', target=t_bot.polling, args=dict(none_stop=True)).start()
        print(bot.botType)
        BotHandlers(bot.id, t_bot, bot.botType)
        self._bots[str(bot.id)] = t_bot
        print(f"Started Bot#{str(bot.id)} - {t_bot}")

