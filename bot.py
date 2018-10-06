import telepot
from os import remove
from time import sleep
from telepot.namedtuple import InlineKeyboardButton, InlineKeyboardMarkup
from telepot.exception import TelegramError
from tinydb import TinyDB, where

bot = telepot.Bot('')   # Bot Token here
group = -1001234567890  # Group ChatID here
db = TinyDB('database.json')


def getInfo(msg):
    msgType, chatType, chatId = telepot.glance(msg)
    msgId = msg['message_id']
    if chatType == "private":
        name = msg['from']['first_name']
        try:
            text = msg['text']
        except KeyError:
            text = None
        try:
            surname = msg['from']['last_name']
        except KeyError:
            surname = ""
        try:
            userStatus = bot.getChatMember(group, chatId)
        except TelegramError:
            userStatus = None
    else:
        text = None
        name = None
        surname = None
        userStatus = None
    return chatId, chatType, msgId, msgType, name, surname, userStatus, text


def rispondi(msg):
    # Parse User Info
    chatId, chatType, msgId, msgType, name, surname, userStatus, text = getInfo(msg)

    # If user that wrote me is in group
    if (chatType is "private") and (userStatus is not None) and (userStatus is not "kicked"):

        # If message is /start, say Hi
        if text == "/start":
            bot.sendMessage(chatId, "Ciao, {0}!\nMandami una foto per postarla sul gruppo.".format(name))

        # If message is a photo
        if msgType is "photo":
            bot.download_file(msg['photo'][0]['file_id'], "foto_{0}".format(msgId))
            bot.sendMessage(chatId, "Grazie, ho ricevuto la foto!")
            message = bot.sendPhoto(group, "foto_{0}".format(msgId), caption="Inviata da <a href=\"tg://user?id={0}\">{1}</a>".format(chatId, name+" "+surname), parse_mode="HTML", reply_markup=None)
            remove("foto_{0}".format(msgId))
            message_id = message['message_id']
            bot.editMessageReplyMarkup((group, message_id), InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="👍 0", callback_data="like#{0}".format(message_id))],
                                 [InlineKeyboardButton(text="👎 0", callback_data="dislike#{0}".format(message_id))]]))
            db.insert({'foto_id': message_id, 'likes': 0, 'dislikes': 0, 'users': []})


def inline_button(msg):
    query_id, fromId, query_data = telepot.glance(msg, flavor="callback_query")
    query_split = query_data.split("#")
    message_id = int(query_split[1])
    button = query_split[0]

    if button is "like":
        prev_data = db.search(where('foto_id') == message_id)[0]
        if fromId not in prev_data['users']:
            db.update({'users': prev_data['users'] + [fromId]}, where('foto_id') == message_id)
            db.update({'likes': prev_data['likes'] + 1}, where('foto_id') == message_id)
            bot.editMessageReplyMarkup((group, message_id), InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="👍 {1}", callback_data="like#{0}".format(message_id, prev_data['likes']+1))],
                                [InlineKeyboardButton(text="👎 {1}", callback_data="dislike#{0}".format(message_id, prev_data['dislikes']))]]))

    elif button is "dislike":
        prev_data = db.search(where('foto_id') == message_id)[0]
        if fromId not in prev_data['users']:
            db.update({'users': prev_data['users'] + [fromId]}, where('foto_id') == message_id)
            db.update({'dislikes': prev_data['dislikes'] + 1}, where('foto_id') == message_id)
            bot.editMessageReplyMarkup((group, message_id), InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="👍 {1}", callback_data="like#{0}".format(message_id, prev_data['likes']))],
                                 [InlineKeyboardButton(text="👎 {1}", callback_data="dislike#{0}".format(message_id, prev_data['dislikes']+1))]]))


bot.message_loop({'chat': rispondi, 'callback_query': inline_button})
while True:
    sleep(60)