import os
import logging
import markovify
import gender_net
import config

import telegram
from telegram.ext import (Updater, CommandHandler, MessageHandler, ConversationHandler, Filters)
from gtts import gTTS

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def generate(text, out_file):
    tts = gTTS(text, lang="ru")
    tts.save(out_file)

def get_model(filename):
    with open(filename, encoding="utf-8") as f:
        text = f.read()

    return markovify.Text(text)

def start(update, context):
    update.message.reply_text("Этот бот умеет определять пол, возраст, а еще курить и материться. Скинь свою реальную фоточку и я скажу, что думаю о тебе")

def error(update, context):
    logger.warning('update "%s" casused error "%s"', update, context.error)

def photo(update, context):
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=telegram.ChatAction.RECORD_AUDIO)

    id = update.message.from_user.id
    name = str(id) + ".jpg"
    filepath = "user_data/" + name

    largest_photo = update.message.photo[-1].get_file()
    largest_photo.download(filepath)

    genders, ages = gender_net.resolve(filepath)
    if len(genders) == 0:
        update.message.reply_text("Отправь сюда фото с людьми, на этой фотографии я их не вижу. Ну ты и дебик.")
        os.remove(filepath)
        return

    out_file = "user_data/" + str(id) + "mp3"
    text = ""
    generator = None

    text = ""
    if gender_net.ageList.index(ages[0]) < 2:
        text = r'Малолетний дебил. Тебя не звали сюда, тебе тут не рады. Это не для тебя делалось и не для таких как ты. Уходи и больше никогда не приходи.'
    elif genders[0] == "female":
        generator = get_model("female")
        text = generator.make_sentence() + r' Выглядишь прекрасно для своих ' + ages[0][1:-1]
    else:
        generator = get_model("male")
        text = generator.make_sentence() + r' Ну и ебало, тебе же всего ' + ages[0][1:-1]


    if text is None:
        text = "Пидор, ты все сломал"


    print(text)

    generate(text, out_file)
    update.message.reply_audio(audio=open(out_file, "rb"))
    os.remove(out_file)
    os.remove(filepath)


def cancel(update, context):
    return ConversationHandler.END

def main():
    updater = Updater(config.token, use_context=True)
    dp = updater.dispatcher

    photo_handler = MessageHandler(Filters.photo, photo)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(photo_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()