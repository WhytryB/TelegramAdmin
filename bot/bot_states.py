from datetime import datetime

import bot.keyboard2 as keyboards
import bot.keyboards as keyboards2
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
    def __init__(self, bot_id, t_bot, botType):
        super(BotStates, self).__init__(bot_id, t_bot, botType)
        self.botType = botType
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
        if self.botType == "fi":
            messId = message.chat.id
        elif self.botType == "sec":
            messId = message.from_user.id
        else:
            messId = ""
        self._bot.send_message(messId,
                               self.get_texts()['greet_msg'])
        cities = City.objects(bot_id=str(self.bot_id))
        print("start")
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
        print("LEADSUmmary")
        if entry:
            print("f11")
            methods.send_leads_summary(self, user)
        else:
            print("s22")
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['back_btn']:
                self._go_to_state(message, self.cities_state)
            elif messText == l_texts['withdraw_btn']:
                self._go_to_state(message, self.leads_withdraw_state)
            elif messText == l_texts['wallet_btn']:
                self._go_to_state(message, self.leads_wallet_state)
            elif messText == l_texts['how_to_btn']:
                self._go_to_state(message, self.leads_how_to_state)
            elif messText == l_texts['request_btn']:
                self._go_to_state(message, self.leads_request_state)
            else:
                if self.botType == "fi":
                    messId = message.chat.id
                    keybd = keyboards2
                elif self.botType == "sec":
                    messId = message.from_user.id
                    keybd = keyboards
                else:
                    messId = ""
                    keybd = ""
                self._bot.send_message(messId,
                                       texts['use_buttons_msg'],
                                       reply_markup=keybd
                                       .set_leads_keyboard(texts, l_texts,
                                                           withdraw_btn=user.balance and user.wallet))

    def leads_withdraw_state(self, message, entry=False):
        print("3333")
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        keyboard = keyboards.set_keyboard(texts, [], back_btn=True)
        if entry:
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            self._bot.send_message(messId,
                                   l_texts['withdraw_reply'],
                                   reply_markup=keybd)
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['back_btn']:
                self._go_to_state(message, self.leads_summary_state)
            else:
                try:
                    wd_sum = int(messText)
                except ValueError:
                    wd_sum = 0
                if user.balance and wd_sum <= user.balance:
                    if wd_sum >= defaults.min_withdraw_sum:
                        WithdrawRequest(user=user, sum=wd_sum).save()
                        self._go_to_state(message, self.leads_summary_state)
                    else:
                        if self.botType == "fi":
                            messId = message.chat.id
                            keybd = keyboards2
                        elif self.botType == "sec":
                            messId = message.from_user.id
                            keybd = keyboards
                        else:
                            messId = ""
                            keybd = ""
                        self._bot.send_message(messId,
                                               l_texts['withdraw_incorrect_sum'],
                                               reply_markup=keybd)
                else:
                    if self.botType == "fi":
                        messId = message.chat.id
                        keybd = keyboards2
                    elif self.botType == "sec":
                        messId = message.from_user.id
                        keybd = keyboards
                    else:
                        messId = ""
                        keybd = ""
                    self._bot.send_message(messId,
                                           l_texts['withdraw_low_balance'],
                                           reply_markup=keybd)

    def leads_request_state(self, message, entry=False):
        print("4444")
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        keyboard = keyboards.set_keyboard(texts, [], back_btn=True)
        if entry:
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            self._bot.send_message(messId,
                                   l_texts['request_reply'],
                                   reply_markup=keybd)
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['back_btn']:
                self._go_to_state(message, self.leads_summary_state)
            else:
                try:
                    p_sum = int(messText.split(' ')[-1])
                except ValueError:
                    p_sum = 0
                if p_sum > 0:
                    if not user.tax:
                        user.tax = defaults.tax
                    p_sum *= user.tax / 100
                    p_sum = round(p_sum)
                    LeadRequest(user=user, code=messText, sum=p_sum, date=datetime.now()).save()
                    self._go_to_state(message, self.leads_summary_state)
                else:
                    if self.botType == "fi":
                        messId = message.chat.id
                        keybd = keyboards2
                    elif self.botType == "sec":
                        messId = message.from_user.id
                        keybd = keyboards
                    else:
                        messId = ""
                        keybd = ""
                    self._bot.send_message(messId,
                                           l_texts['request_incorrect_sum'],
                                           reply_markup=keybd)

    def leads_wallet_state(self, message, entry=False):
        print("555")
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        if entry:
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            self._bot.send_message(messId,
                                   l_texts['wallet_reply'],
                                   reply_markup=keybd.set_keyboard(texts, [], back_btn=True))
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText != texts['back_btn']:
                user.wallet = messText
                user.save()
            self._go_to_state(message, self.leads_summary_state)

    def leads_how_to_state(self, message, entry=False):
        print("66666")
        user = self.get_user(message)
        l_texts = self.get_lead_texts()
        texts = self.get_texts()
        if self.botType == "fi":
            messText = message.text
        elif self.botType == "sec":
            messText = message.data
        else:
            messText = ""
        if entry:
            file = l_texts['how_to_reply_file']
            img = l_texts['how_to_reply_image']
            text = l_texts['how_to_reply']
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            if file:
                self._bot.send_document(user.user_id,
                                        file,
                                        caption=text,
                                        reply_markup=keybd.set_keyboard(texts, [], back_btn=True),
                                        parse_mode='markdown')
            elif img:
                self._bot.send_photo(user.user_id,
                                     img.read(),
                                     caption=text,
                                     reply_markup=keybd.set_keyboard(texts, [], back_btn=True),
                                     parse_mode='markdown')
            else:
                self._bot.send_message(messId,
                                       text,
                                       reply_markup=keybd.set_keyboard(texts, [], back_btn=True))
        elif messText == texts['back_btn']:
            self._go_to_state(message, self.leads_summary_state)

    def cities_state(self, message, entry=False):
        cities = group_by_name(City.objects(bot_id=str(self.bot_id)))
        texts = self.get_texts()
        user = self.get_user(message)
        if entry:
            print("fi")
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            self._bot.send_message(messId,
                                   texts['choose_city_msg'],
                                   reply_markup=keybd.set_keyboard(texts, cities.keys(),
                                                                       leads_btn=user.is_admin))
        else:
            print("se")
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if cities.get(messText):
                user.city = cities.get(messText)
                user.save()
                self._go_to_state(message, self.goods_state)
            elif messText == texts['leads_btn'] and user.is_admin:
                self._go_to_state(message, self.leads_summary_state)
            else:
                if self.botType == "fi":
                    messId = message.chat.id
                    keybd = keyboards2
                elif self.botType == "sec":
                    messId = message.from_user.id
                    keybd = keyboards
                else:
                    messId = ""
                    keybd = ""
                self._bot.send_message(messId,
                                       texts['use_buttons_msg'],
                                       reply_markup=keybd.set_keyboard(texts, cities.keys(),
                                                                           leads_btn=user.is_admin))

    def districts_state(self, message, entry=False):
        print("77777")
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

            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            keyboard = keybd.set_keyboard(texts, districts.keys(), back_btn=True)
            try:

                if good.photo:
                    self._bot.send_photo(messId,
                                         good.photo.read(),
                                         caption=message_text,
                                         reply_markup=keyboard,
                                         parse_mode='markdown')

                else:
                    self._bot.send_message(messId,
                                           message_text,
                                           reply_markup=keyboard,
                                           parse_mode='markdown')
            except:
                self._bot.send_message(messId,
                                       message_text,
                                       reply_markup=keyboard,
                                       parse_mode='markdown')
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['back_btn']:
                self._go_to_state(message, self.goods_state)
            else:
                if districts.get(messText):
                    user.district = districts.get(messText)
                    user.save()
                    self._go_to_state(message, self.payment_state)
                else:
                    if self.botType == "fi":
                        messId = message.chat.id
                        keybd = keyboards2
                    elif self.botType == "sec":
                        messId = message.from_user.id
                        keybd = keyboards
                    else:
                        messId = ""
                        keybd = ""
                    self._bot.send_message(messId,
                                           texts['use_buttons_msg'],
                                           reply_markup=keybd.set_keyboard(texts, districts.keys(), back_btn=True))

    def goods_state(self, message, entry=False):
        texts = self.get_texts()
        user = self.get_user(message)
        print("god")
        goods = group_by_name(Good.objects(city_id=str(user.city.id)))
        if self.botType == "fi":
            messId = message.chat.id
            keybd = keyboards2
        elif self.botType == "sec":
            messId = message.from_user.id
            keybd = keyboards
        else:
            messId = ""
            keybd = ""
        if entry:
            print("su1")
            self._bot.send_message(messId,
                                   texts['choose_good_msg'],
                                   reply_markup=keybd.set_keyboard(texts, goods.keys(), back_btn=True))
        else:
            print("su2")
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['back_btn']:
                self._go_to_state(message, self.cities_state)
            else:
                good = goods.get(messText)
                if good:
                    user.good = good
                    user.clicked_goods.append(good)
                    user.save()
                    self._go_to_state(message, self.districts_state)
                else:
                    self._bot.send_message(messId,
                                           texts['use_buttons_msg'],
                                           reply_markup=keybd.set_keyboard(texts, goods.keys(), back_btn=True))

    def payment_state(self, message, entry=False):
        print("9999")
        texts = self.get_texts()
        user = self.get_user(message)
        payments = group_by(Payment.objects(bot_id=str(self.bot_id)), 'payment_name')
        if entry:
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            self._bot.send_message(messId,
                                   texts['choose_payment_msg'],
                                   reply_markup=keybd.set_keyboard(texts, payments.keys(), back_btn=True))
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if payments.get(messText):
                user.payment = payments.get(messText)
                user.save()
                self._go_to_state(message, self.final_state)
            elif messText == texts['back_btn']:
                self._go_to_state(message, self.districts_state)
            else:
                if self.botType == "fi":
                    messId = message.chat.id
                    keybd = keyboards2
                elif self.botType == "sec":
                    messId = message.from_user.id
                    keybd = keyboards
                else:
                    messId = ""
                    keybd = ""
                self._bot.send_message(messId,
                                       texts['use_buttons_msg'],
                                       reply_markup=keybd.set_keyboard(texts, payments.keys(), back_btn=True))

    def final_state(self, message, entry=False):
        print("000011112")
        texts = self.get_texts()
        user = self.get_user(message)
        if entry:
            if self.botType == "fi":
                messId = message.chat.id
                keybd = keyboards2
            elif self.botType == "sec":
                messId = message.from_user.id
                keybd = keyboards
            else:
                messId = ""
                keybd = ""
            bot = BotProfile.objects(id=self.bot_id).first()
            text = Payment.objects(id=user.payment.id).first().answer_text.replace('#wallet#', bot.wallet)
            self._bot.send_message(messId,
                                   text,
                                   reply_markup=keybd.set_keyboard(texts, [], back_btn=True, done_btn=True))
        else:
            if self.botType == "fi":
                messText = message.text
            elif self.botType == "sec":
                messText = message.data
            else:
                messText = ""
            if messText == texts['done_btn']:
                methods.create_order(self, user)
                self._go_to_state(message, self.districts_state)
            elif messText == texts['back_btn']:
                self._go_to_state(message, self.payment_state)
            else:
                if self.botType == "fi":
                    messId = message.chat.id
                    keybd = keyboards2
                elif self.botType == "sec":
                    messId = message.from_user.id
                    keybd = keyboards
                else:
                    messId = ""
                    keybd = ""
                text = Payment.objects(id=user.payment.id).first().answer_on_payment
                self._bot.send_message(messId,
                                       text,
                                       reply_markup=keybd.set_keyboard(texts, [], back_btn=True))
                user.code = messText
                user.save()
                methods.create_order(self, user)