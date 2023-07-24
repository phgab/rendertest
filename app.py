import os
import signal
import asyncio
from typing import Optional, Awaitable

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import telebot

#new
import logging
from telegram.ext import Updater
from convHandlerBike import getConvHandlerBike
from convHandlerWeather import getConvHandlerWeather
from stdBotCommands import addBotCommands

API_TOKEN = os.environ['TELE_BOT']
WEBHOOK_HOST = os.environ['TELE_BOT_URL']
WEBHOOK_SECRET = "setwebhook"
WEBHOOK_PORT = 8000
#WEBHOOK_URL_BASE = f"https://{0}:{1}/{2}".format(WEBHOOK_HOST, str(WEBHOOK_PORT), WEBHOOK_SECRET)
WEBHOOK_URL_BASE = "{0}/{1}".format(WEBHOOK_HOST, WEBHOOK_SECRET)


tornado.options.define("port", default=WEBHOOK_PORT, help="run on the given port", type=int)

# bot = telebot.TeleBot(API_TOKEN)
# new start
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
updater = Updater(API_TOKEN, use_context=True)
#new end

class BaseHandler(tornado.web.RequestHandler):
    """
    Base handler gonna to be used instead of RequestHandler
    """
    def write_error(self, status_code, **kwargs):
        if status_code in [403, 404, 500, 503]:
            self.write('Error %s' % status_code)
        else:
            self.write('BOOM!')

class ErrorHandler(tornado.web.ErrorHandler, BaseHandler):
    """
    Default handler gonna to be used in case of 404 error
    """
    pass


class Root(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        self.write("Hi! This is webhook example!")
        self.finish()


class WebhookServ(BaseHandler):
    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def get(self):
        self.write("What are you doing here?")
        self.finish()

    def post(self):
        if "Content-Length" in self.request.headers and \
            "Content-Type" in self.request.headers and \
            self.request.headers['Content-Type'] == "application/json":

            # length = int(self.request.headers['Content-Length'])
            json_data = self.request.body.decode("utf-8")
            update = telebot.types.Update.de_json(json_data)
            bot.process_new_updates([update])
            self.write("")
            self.finish()
        else:
            self.write("What are you doing here?")
            self.finish()


# # Handle '/start' and '/help'
# @bot.message_handler(commands=['help', 'start'])
# def send_welcome(message):
#     bot.reply_to(message,
#                  ("Hi there, I am EchoBot.\n"
#                   "I am here to echo your kind words back to you."))
#
# @bot.message_handler(commands=['greet'])
# def greet(message):
#     bot.send_message(message.chat.id, "Hey how's it going?")
#
#
# def dict_definition(message):
#     request = message.text.split()
#     if len(request) < 2: #or request[0].lower() not in "price":
#         return False
#     else:
#         return True
#
# @bot.message_handler(func=dict_definition)
# def vocab_def(message):
#     print(f"message: {message}")
#     bot.send_message(message.chat.id, f"message: {message.text}")


def make_app():
    # bot.remove_webhook()
    # print(WEBHOOK_URL_BASE)
    # bot.set_webhook(url=WEBHOOK_URL_BASE)

    # new start
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Conversation handlers
    dp.add_handler(getConvHandlerWeather())

    dp.add_handler(getConvHandlerBike())

    # Standard commands
    dp = addBotCommands(dp, logger)

    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(WEBHOOK_PORT),
                          url_path=API_TOKEN)
    updater.bot.setWebhook(WEBHOOK_URL_BASE + API_TOKEN)

    updater.bot.sendMessage(532298931, "Bot running")
    # new end

    #signal.signal(signal.SIGINT, signal_handler)
    settings = dict(
        cookie_secret=str(os.urandom(45)),
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        default_handler_class=ErrorHandler,
        default_handler_args=dict(status_code=404)
    )
    return tornado.web.Application([
            (r"/", Root),
            (r"/" + WEBHOOK_SECRET, WebhookServ)
        ], **settings)

async def main():
    print("starting tornado server..........")
    app = make_app()
    app.listen(tornado.options.options.port)
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())