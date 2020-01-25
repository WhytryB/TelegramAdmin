from telebot import types


def set_keyboard(texts, rows, done_btn=False, back_btn=False, leads_btn=False):
    keyboard = types.InlineKeyboardMarkup()
    if rows is not None:
        for i in rows:
            keyboard.add(types.InlineKeyboardButton(text=i, callback_data=i))
    if done_btn:
        keyboard.add(types.InlineKeyboardButton(text=texts['done_btn'],  callback_data=texts['done_btn']))
    if back_btn:
        keyboard.add(types.InlineKeyboardButton(text=texts['back_btn'],  callback_data=texts['back_btn']))
    if leads_btn:
        keyboard.add(types.InlineKeyboardButton(text=texts['leads_btn'],  callback_data=texts['leads_btn']))
    return keyboard


def set_leads_keyboard(texts, l_texts, withdraw_btn=False):
    keyboard = types.InlineKeyboardMarkup()
    wallet_btn = l_texts['wallet_btn']
    if withdraw_btn:
        keyboard.add(types.InlineKeyboardButton(wallet_btn, l_texts['withdraw_btn']))
    else:
        keyboard.add(types.InlineKeyboardButton(text=wallet_btn, callback_data=wallet_btn))
    keyboard.add(types.InlineKeyboardButton(text=l_texts['how_to_btn'], callback_data=l_texts['how_to_btn']))
    keyboard.add(types.InlineKeyboardButton(text=l_texts['request_btn'], callback_data=l_texts['request_btn']))
    keyboard.add(types.InlineKeyboardButton(text=texts['back_btn'], callback_data=texts['back_btn']))
    return keyboard


def remove_keyboard():
    keyboard = types.ReplyKeyboardRemove()
    return keyboard
