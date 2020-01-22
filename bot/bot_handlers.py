from bot.bot_states import BotStates
from logger_settings import logger
from telebot import types
import bot


class BotHandlers(object):

    def __init__(self, bot_id, t_bot, botType):
        self.botType = botType
        self.bot_id = bot_id
        self.bot = t_bot
        self.__bot_state_handler = BotStates(bot_id, self.bot, botType)
        self.__start_handling()

    def __start_handling(self):

        @self.bot.message_handler(commands=['start'])
        def send_welcome(message):
            try:
                self.__bot_state_handler.handle_state_with_message(message, start=True)
            except Exception as e:
                logger.error(f'[ERROR] {e}')

        @self.bot.message_handler(content_types=['text'])
        def text_handler(message):
            print("suka1")
            try:
                if self.botType == "fi":
                    self.bot.send_chat_action(message.chat.id, 'typing')
                    self.__bot_state_handler.handle_state_with_message(message)
            except Exception as e:
                print(e)
                logger.exception('[ERROR]')

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            print("suja2")
            try:
                if call.data:
                    if self.botType == "sec":
                        self.bot.answer_callback_query(call.id)
                        self.bot.send_chat_action(call.from_user.id, 'typing')
                        self.__bot_state_handler.handle_state_with_message(call)
                    print(call.data)
            except:
                logger.exception('[ERROR]')

        # @self.bot.inline_handler(func=lambda query: len(query.query) > 0)
        # def query_text(query):
        #     try:
        #         self.bot.answer_inline_query(query.id, keyboards.set_chat_share_button(query.from_user.id))
        #     except:
        #         logger.exception('[ERROR]')
