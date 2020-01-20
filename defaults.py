from models import Texts, LeadTexts


BACKBTN = 'Назад'
USEBUTTONS = 'Используй только кнопки'
CHOOSEGOOD = 'Выбери товар'
CHOOSESITY =  'Выбери город'
CHOOSEDISTRICT =  'Выбери район'
CHOOSEPAYMENT = 'Выбери способ оплаты'
DONE = 'Готово'
LEADS = 'Лиды'
NEWORDER = 'Новый заказ ID: {}\n' \
                      'Имя Фамилия: {} {}\n' \
                      'Username: {}\n' \
                      'Город: {}\n' \
                      'Район: {}\n' \
                      'Товар: {}\n' \
                      'Оплата: {}\n' \
                      'Код: {}'
SELECTED = 'Выбрано: *{}*\n' \
                          'Коротко о товаре: *{}*\n' \
                          'Цена: *{}* грн.\n\n' \
                          'Выбирай район:'
SELECTED2 = 'Выбрано: *{}*\n' \
                          'Коротко о товаре: *{}*\n' \
                          'Старая цена: *{}* грн.\n' \
                          'Новая цена: *{}* грн.\n\n' \
                           'Выбирай район:'

texts = Texts()
texts.greet_msg = 'Привет'
texts.back_btn = BACKBTN
texts.use_buttons_msg = USEBUTTONS
texts.choose_good_msg = CHOOSEGOOD
texts.choose_city_msg = CHOOSESITY
texts.choose_district_msg = CHOOSEDISTRICT
texts.choose_payment_msg = CHOOSEPAYMENT
texts.done_btn = DONE
texts.leads_btn = LEADS
texts.new_order_msg = NEWORDER
texts.selected_good_msg2 = SELECTED2
texts.selected_good_msg = SELECTED

l_texts = LeadTexts()
l_texts.wallet_btn = 'Кошелек'
l_texts.wallet_reply = 'Введи кошелек'
l_texts.withdraw_btn = 'Заказать выплату'
l_texts.withdraw_reply = 'Введи сумму'
l_texts.withdraw_incorrect_sum = 'Минимальная сумма - 500'
l_texts.withdraw_low_balance = 'Низкий баланс'
l_texts.how_to_btn = 'Как привлечь трафик?'
l_texts.how_to_reply = 'Вот так.'
l_texts.request_btn = 'Отправить лид на проверку'
l_texts.request_reply = 'Введи код (команду)'
l_texts.request_incorrect_sum = 'Некорректная сумма платежа'
l_texts.summary_msg = 'Ставка: *{}%*\n' \
                      'Всего лидов: *{}*\n' \
                      'Сегодня: *{}*\n' \
                      'В обработке: *{}*\n' \
                      'Одобрено: *{}*\n' \
                      'К выводу: *{}* грн.'

tax = 50
min_withdraw_sum = 500
