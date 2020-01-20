from time import sleep

from datetime import datetime
from telebot import types

import defaults
from bot import keyboards
from models import User, Texts, Order, LeadTexts, LeadRequest


def create_order(self, user):
    user.ordered_goods.append(user.good)
    user.save()
    order = Order(user=user,
                  city_name=user.city.name,
                  district_name=user.district.name,
                  good_name=user.good.name,
                  payment_name=user.payment.payment_name,
                  code=user.code)
    order.save()
    notify_admins(self, order)


def send_leads_summary(self, user):
    texts = Texts.objects().first()
    l_texts = LeadTexts.objects().first()
    if not user.tax:
        user.tax = defaults.tax
    l_requests = LeadRequest.objects(user=user)
    total = len(l_requests)
    today = len([r for r in l_requests if r.date.date() == datetime.today().date()])
    pending = len([r for r in l_requests if not r.approved])
    approved = len([r for r in l_requests if r.approved])
    self._bot.send_message(user.user_id,
                           l_texts['summary_msg'].format(user.tax,
                                                         total,
                                                         today,
                                                         pending,
                                                         approved,
                                                         user.balance),
                           reply_markup=keyboards.set_leads_keyboard(texts, l_texts,
                                                                     withdraw_btn=user.balance and user.wallet),
                           parse_mode='markdown')


def notify_admins(self, order):
    admins = User.objects(bot=order.user.bot, is_admin=True)
    texts = Texts.objects(bot_id=str(order.user.bot.id)).first()

    if not admins:
        return

    for admin in admins:
        if order.user.username:
            username = f'@{order.user.username}'
        else:
            username = 'None'
        message_text = texts['new_order_msg'].format(order.user.user_id,
                                                     order.user.first_name,
                                                     order.user.last_name,
                                                     username,
                                                     order.city_name,
                                                     order.district_name,
                                                     order.good_name,
                                                     order.payment_name,
                                                     order.code)
        self._bot.send_message(admin.user_id, message_text, parse_mode='markdown')


def send_messages(bot_id, bot, message):
    users = User.objects(bot=bot_id)
    amount = users.count()

    if message.url and message.url_text:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(types.InlineKeyboardButton(text=message.url_text, url=message.url))
    else:
        keyboard = None

    photo = message.image.read()
    file = message.file
    if message.markup:
        markdown = 'markdown'
    else:
        markdown = None

    for user in users[:1000]:
        try:
            if photo:
                if keyboard is not None:
                    last_message = bot.send_photo(user.user_id,
                                                  photo,
                                                  caption=message.text,
                                                  reply_markup=keyboard,
                                                  parse_mode=markdown)
                else:
                    last_message = bot.send_photo(user.user_id,
                                                  photo,
                                                  caption=message.text,
                                                  parse_mode=markdown)
                photo = last_message.photo[-1].file_id
            elif file:
                if keyboard is not None:
                    last_message = bot.send_document(user.user_id,
                                                     file,
                                                     caption=message.text,
                                                     reply_markup=keyboard,
                                                     parse_mode=markdown)
                else:
                    last_message = bot.send_document(user.user_id,
                                                     file,
                                                     caption=message.text,
                                                     parse_mode=markdown)
                file = last_message.document.file_id
            elif keyboard is not None:
                last_message = bot.send_message(user.user_id,
                                                message.text,
                                                reply_markup=keyboard,
                                                parse_mode=markdown)
            else:
                last_message = bot.send_message(user.user_id,
                                                message.text,
                                                parse_mode=markdown)

        except Exception as ex:
            print(f'{user} blocked this bot')

    if amount > 1000:
        for thousand in range(1, amount // 1000 + 1):
            sleep(60)
            for user in users[thousand * 1000:(thousand + 1) * 1000]:
                try:
                    if photo:
                        if keyboard is not None:
                            bot.send_photo(user.user_id, photo,
                                           caption=message.text,
                                           reply_markup=keyboard,
                                           parse_mode=markdown)
                        else:
                            bot.send_photo(user.user_id,
                                           photo,
                                           caption=message.text,
                                           parse_mode=markdown)
                    elif file:
                        if keyboard is not None:
                            bot.send_document(user.user_id,
                                              file,
                                              caption=message.text,
                                              reply_markup=keyboard,
                                              parse_mode=markdown)
                        else:
                            bot.send_document(user.user_id,
                                              file,
                                              caption=message.text,
                                              parse_mode=markdown)
                    else:
                        if keyboard is not None:
                            bot.send_message(user.user_id,
                                             message.text,
                                             reply_markup=keyboard,
                                             parse_mode=markdown)
                        else:
                            bot.send_message(user.user_id,
                                             message.text,
                                             parse_mode=markdown)
                except:
                    print(f'{user} blocked this bot')
