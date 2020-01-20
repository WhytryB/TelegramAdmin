from types import FunctionType

from telebot import TeleBot

from models import User

from datetime import datetime

class StateHandler(object):

    def __init__(self, bot_id, bot: TeleBot):
        self.bot_id = bot_id
        self._bot = bot
        self.__state_functions = {'start': self._start_state}

    def _start_state(self, message):
        try:
            self._bot.send_message(message.chat.id, 'Welcome message')
        except Exception as e:
            print('[Error]{0}'.format(e))

    def get_user_query(self, message):
        return User.objects(bot=self.bot_id, user_id=message.chat.id)

    def get_user(self, message):
        return self.get_user_query(message).first()

    def handle_state_with_message(self, message, start=False):
        user = self.get_user(message)
        if user is None:
            user = User(bot=self.bot_id,
                        user_id=message.chat.id,
                        first_name=str(message.from_user.first_name),
                        last_name=str(message.from_user.last_name),
                        username=str(message.from_user.username),
                        state='start', datetime=datetime.now()).save()
        if start:
            user.state = 'start'
        self.__state_functions[user['state']](message)

    def __register_state(self, name, function_pointer: FunctionType):
        if name != '' and function_pointer is not None:
            self.__state_functions[name] = function_pointer

    def _register_states(self, states_list):
        for state_func in states_list:
            self.__register_state(state_func.__name__, state_func)

    def _go_to_state(self, message, state_name):
        if str(type(state_name)) == "<class 'method'>":
            state_name = state_name.__name__
        if state_name in self.__state_functions:
            self.get_user_query(message).update_one(state=state_name)
            self.__state_functions[state_name](message, entry=True)
        else:
            print('[Warning] No state with name "{}"'.format(state_name))
            self.get_user_query(message).update_one(state='start')
            self.__state_functions[state_name](message, entry=True)
