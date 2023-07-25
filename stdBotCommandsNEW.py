from datetime import datetime
from telegram.ext import CommandHandler, MessageHandler, filters
import os


def addBotCommands(dp, log):

    global logger
    logger = log

    # Standard commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("time", time))
    dp.add_handler(CommandHandler("chatID", chatID))
    dp.add_handler(CommandHandler("sendPickle", sendPickle))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(filters.TEXT, echo))

    # log all errors
    dp.add_error_handler(error)

    return dp


def sendPickle(update, context):
    if os.path.isfile("weatherData"):
        bot = context.bot
        bot.send_document(update.message.chat.id, open("weatherData", 'rb'))
        update.message.reply_text("There you go")
    else:
        update.message.reply_text("No file saved")


def echo(update, context):
    """Echo the user message."""
    update.message.reply_text(update.message.text)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def time(update, context):
    """Returns the time"""
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    update.message.reply_text(current_time)


def start(update, context):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help(update, context):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def chatID(update, context):
    update.message.reply_text(update.message.chat.id)

