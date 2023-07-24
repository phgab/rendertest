import logging
from telegram.ext import Updater
import os
from convHandlerBike import getConvHandlerBike
from convHandlerWeather import getConvHandlerWeather
from stdBotCommands import addBotCommands

PORT = int(os.environ.get('PORT', 5000))

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)
TOKEN = os.environ["TELTOKEN"]

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
#gb: test for heroku update

def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher


    # Conversation handlers
    dp.add_handler(getConvHandlerWeather())

    dp.add_handler(getConvHandlerBike())


    # Standard commands
    dp = addBotCommands(dp, logger)


    # Start the Bot
    updater.start_webhook(listen="0.0.0.0",
                          port=int(PORT),
                          url_path=TOKEN)
    updater.bot.setWebhook('https://fine-ruby-piglet-coat.cyclic.app/' + TOKEN)
    # updater.bot.setWebhook('https://gbweatherbot.herokuapp.com/' + TOKEN)
    
    updater.bot.sendMessage(532298931,"Bot running")
    print('test')
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()
