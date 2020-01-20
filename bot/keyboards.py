from telebot import types


def set_keyboard(texts, rows, done_btn=False, back_btn=False, leads_btn=False):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if rows is not None:
        for row in rows:
            keyboard.row(row)
    if done_btn:
        keyboard.row(texts['done_btn'])
    if back_btn:
        keyboard.row(texts['back_btn'])
    if leads_btn:
        keyboard.row(texts['leads_btn'])
    return keyboard


def set_leads_keyboard(texts, l_texts, withdraw_btn=False):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    wallet_btn = l_texts['wallet_btn']
    if withdraw_btn:
        keyboard.row(wallet_btn, l_texts['withdraw_btn'])
    else:
        keyboard.row(wallet_btn)
    keyboard.row(l_texts['how_to_btn'])
    keyboard.row(l_texts['request_btn'])
    keyboard.row(texts['back_btn'])
    return keyboard


def remove_keyboard():
    keyboard = types.ReplyKeyboardRemove()
    return keyboard
