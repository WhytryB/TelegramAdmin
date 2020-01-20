from datetime import datetime

import bot.keyboards as keyboards
import defaults
from admin import methods
from bot.state_handler import StateHandler
from models import Texts, Payment, City, Good, LeadTexts, WithdrawRequest, LeadRequest, BotProfile


def group_by(coll, attr_name):
    result = dict()
    for e in coll:
        result[e[attr_name]] = e
    return result


def group_by_name(coll):
    return group_by(coll, 'name')


class BotStates(StateHandler):
    def __init__(self, bot_id, t_bot):
        super(BotStates, self).__init__(bot_id, t_bot)
        self._register_states([self.leads_summary_state,
                               self.leads_withdraw_state,
                               self.leads_wallet_state,
                               self.leads_how_to_state,
                               self.leads_request_state,
                               self.cities_state,
                               self.districts_state,
                               self.goods_state,
                               self.payment_state,
                               self.final_state])

    def get_texts(self):
        return Texts.objects(bot_id=str(self.bot_id)).first()

    def get_lead_texts(self):
        return LeadTexts.objects().first()

    def _start_state(self, message, entry=False):
        self._bot.send_message(message.chat.id,
                               self.get_texts()['greet_msg'])
        cities = City.objects(bot_id=str(self.bot_id))
        if not cities:
            return
        if len(cities) == 1:
            user = self.get_user(message)
            user.city = cities[0]
            user.save()
            self._go_to_state(message, self.goods_state)
        else:
            self._go_to_state(message, self.cities_state)

    def leads_summary_state(self, message, entry=False):
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        if entry:
            methods.send_leads_summary(self, user)
        else:
            if message.text == texts['back_btn']:
                self._go_to_state(message, self.cities_state)
            elif message.text == l_texts['withdraw_btn']:
                self._go_to_state(message, self.leads_withdraw_state)
            elif message.text == l_texts['wallet_btn']:
                self._go_to_state(message, self.leads_wallet_state)
            elif message.text == l_texts['how_to_btn']:
                self._go_to_state(message, self.leads_how_to_state)
            elif message.text == l_texts['request_btn']:
                self._go_to_state(message, self.leads_request_state)
            else:
                self._bot.send_message(message.chat.id,
                                       texts['use_buttons_msg'],
                                       reply_markup=keyboards
                                       .set_leads_keyboard(texts, l_texts,
                                                           withdraw_btn=user.balance and user.wallet))

    def leads_withdraw_state(self, message, entry=False):
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        keyboard = keyboards.set_keyboard(texts, [], back_btn=True)
        if entry:
            self._bot.send_message(message.chat.id,
                                   l_texts['withdraw_reply'],
                                   reply_markup=keyboard)
        else:
            if message.text == texts['back_btn']:
                self._go_to_state(message, self.leads_summary_state)
            else:
                try:
                    wd_sum = int(message.text)
                except ValueError:
                    wd_sum = 0
                if user.balance and wd_sum <= user.balance:
                    if wd_sum >= defaults.min_withdraw_sum:
                        WithdrawRequest(user=user, sum=wd_sum).save()
                        self._go_to_state(message, self.leads_summary_state)
                    else:
                        self._bot.send_message(message.chat.id,
                                               l_texts['withdraw_incorrect_sum'],
                                               reply_markup=keyboard)
                else:
                    self._bot.send_message(message.chat.id,
                                           l_texts['withdraw_low_balance'],
                                           reply_markup=keyboard)

    def leads_request_state(self, message, entry=False):
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        keyboard = keyboards.set_keyboard(texts, [], back_btn=True)
        if entry:
            self._bot.send_message(message.chat.id,
                                   l_texts['request_reply'],
                                   reply_markup=keyboard)
        else:
            if message.text == texts['back_btn']:
                self._go_to_state(message, self.leads_summary_state)
            else:
                try:
                    p_sum = int(message.text.split(' ')[-1])
                except ValueError:
                    p_sum = 0
                if p_sum > 0:
                    if not user.tax:
                        user.tax = defaults.tax
                    p_sum *= user.tax / 100
                    p_sum = round(p_sum)
                    LeadRequest(user=user, code=message.text, sum=p_sum, date=datetime.now()).save()
                    self._go_to_state(message, self.leads_summary_state)
                else:
                    self._bot.send_message(message.chat.id,
                                           l_texts['request_incorrect_sum'],
                                           reply_markup=keyboard)

    def leads_wallet_state(self, message, entry=False):
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        if entry:
            self._bot.send_message(message.chat.id,
                                   l_texts['wallet_reply'],
                                   reply_markup=keyboards.set_keyboard(texts, [], back_btn=True))
        else:
            if message.text != texts['back_btn']:
                user.wallet = message.text
                user.save()
            self._go_to_state(message, self.leads_summary_state)

    def leads_how_to_state(self, message, entry=False):
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        if entry:
            file = l_texts['how_to_reply_file']
            img = l_texts['how_to_reply_image']
            text = l_texts['how_to_reply']
            if file:
                self._bot.send_document(user.user_id,
                                        file,
                                        caption=text,
                                        reply_markup=keyboards.set_keyboard(texts, [], back_btn=True),
                                        parse_mode='markdown')
            elif img:
                self._bot.send_photo(user.user_id,
                                     img.read(),
                                     caption=text,
                                     reply_markup=keyboards.set_keyboard(texts, [], back_btn=True),
                                     parse_mode='markdown')
            else:
                self._bot.send_message(message.chat.id,
                                       text,
                                       reply_markup=keyboards.set_keyboard(texts, [], back_btn=True))
        elif message.text == texts['back_btn']:
            self._go_to_state(message, self.leads_summary_state)

    def cities_state(self, message, entry=False):
        cities = group_by_name(City.objects(bot_id=str(self.bot_id)))
        texts = self.get_texts()
        user = self.get_user(message)
        if entry:
            self._bot.send_message(message.chat.id,
                                   texts['choose_city_msg'],
                                   reply_markup=keyboards.set_keyboard(texts, cities.keys(),
                                                                       leads_btn=user.is_admin))
        else:
            if cities.get(message.text):
                user.city = cities.get(message.text)
                user.save()
                self._go_to_state(message, self.goods_state)
            elif message.text == texts['leads_btn'] and user.is_admin:
                self._go_to_state(message, self.leads_summary_state)
            else:
                self._bot.send_message(message.chat.id,
                                       texts['use_buttons_msg'],
                                       reply_markup=keyboards.set_keyboard(texts, cities.keys(),
                                                                           leads_btn=user.is_admin))

    def districts_state(self, message, entry=False):
        user = self.get_user(message)
        good = user.good
        districts = group_by_name(good.districts)
        texts = self.get_texts()
        if entry:
            if int(good.sale) > 0:
                selected_good_msg2 ='Выбрано: *{}*\n' \
                                  'Коротко о товаре: *{}*\n' \
                                  'Старая цена: *{}* грн.\n' \
                                  'Новая цена: *{}* грн.\n\n' \
                                   'Выбирай район:'
                message_text = selected_good_msg2.format(good.name, good.description, good.price,
                                                         good.PriceWithSale)
            else:
                message_text = texts['selected_good_msg'].format(good.name, good.description, good.price)
            keyboard = keyboards.set_keyboard(texts, districts.keys(), back_btn=True)
            try:
                if good.photo:
                    self._bot.send_photo(message.chat.id,
                                         good.photo.read(),
                                         caption=message_text,
                                         reply_markup=keyboard,
                                         parse_mode='markdown')

                else:
                    self._bot.send_message(message.chat.id,
                                           message_text,
                                           reply_markup=keyboard,
                                           parse_mode='markdown')
            except:
                self._bot.send_message(message.chat.id,
                                       message_text,
                                       reply_markup=keyboard,
                                       parse_mode='markdown')
        else:
            if message.text == texts['back_btn']:
                self._go_to_state(message, self.goods_state)
            else:
                if districts.get(message.text):
                    user.district = districts.get(message.text)
                    user.save()
                    self._go_to_state(message, self.payment_state)
                else:
                    self._bot.send_message(message.chat.id,
                                           texts['use_buttons_msg'],
                                           reply_markup=keyboards.set_keyboard(texts, districts.keys(), back_btn=True))

    def goods_state(self, message, entry=False):
        texts = self.get_texts()
        user = self.get_user(message)
        goods = group_by_name(Good.objects(city_id=str(user.city.id)))
        if entry:
            self._bot.send_message(message.chat.id,
                                   texts['choose_good_msg'],
                                   reply_markup=keyboards.set_keyboard(texts, goods.keys(), back_btn=True))
        else:
            if message.text == texts['back_btn']:
                self._go_to_state(message, self.cities_state)
            else:
                good = goods.get(message.text)
                if good:
                    user.good = good
                    user.clicked_goods.append(good)
                    user.save()
                    self._go_to_state(message, self.districts_state)
                else:
                    self._bot.send_message(message.chat.id,
                                           texts['use_buttons_msg'],
                                           reply_markup=keyboards.set_keyboard(texts, goods.keys(), back_btn=True))

    def payment_state(self, message, entry=False):
        texts = self.get_texts()
        user = self.get_user(message)
        payments = group_by(Payment.objects(bot_id=str(self.bot_id)), 'payment_name')
        if entry:
            self._bot.send_message(message.chat.id,
                                   texts['choose_payment_msg'],
                                   reply_markup=keyboards.set_keyboard(texts, payments.keys(), back_btn=True))
        else:
            if payments.get(message.text):
                user.payment = payments.get(message.text)
                user.save()
                self._go_to_state(message, self.final_state)
            elif message.text == texts['back_btn']:
                self._go_to_state(message, self.districts_state)
            else:
                self._bot.send_message(message.chat.id,
                                       texts['use_buttons_msg'],
                                       reply_markup=keyboards.set_keyboard(texts, payments.keys(), back_btn=True))

    def final_state(self, message, entry=False):
        texts = self.get_texts()
        user = self.get_user(message)
        if entry:
            bot = BotProfile.objects(id=self.bot_id).first()
            text = Payment.objects(id=user.payment.id).first().answer_text.replace('#wallet#', bot.wallet)
            self._bot.send_message(message.chat.id,
                                   text,
                                   reply_markup=keyboards.set_keyboard(texts, [], back_btn=True, done_btn=True))
        else:
            if message.text == texts['done_btn']:
                methods.create_order(self, user)
                self._go_to_state(message, self.districts_state)
            elif message.text == texts['back_btn']:
                self._go_to_state(message, self.payment_state)
            else:
                text = Payment.objects(id=user.payment.id).first().answer_on_payment
                self._bot.send_message(message.chat.id,
                                       text,
                                       reply_markup=keyboards.set_keyboard(texts, [], back_btn=True))
                user.code = message.text
                user.save()
                methods.create_order(self, user)