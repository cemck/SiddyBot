from uuid import uuid4
from telegram.utils.helpers import escape_markdown
from telegram import ParseMode, InputTextMessageContent, InlineQueryResultArticle, InlineQueryResultVoice, ReplyKeyboardMarkup, ReplyKeyboardRemove, Chat
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, ConversationHandler, MessageHandler, Filters, RegexHandler
import configparser as cfg
import logging
import glob
import os

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

VOICE, NAME = range(2)

### Helper functions ###


def read_token_from_config_file(config):
    parser = cfg.ConfigParser()
    parser.read(config)
    return parser.get('creds', 'token')


def voice_files_to_str(voice_files):
    voice_list = list()

    if not voice_files:
        return None
    for ele in voice_files:
        new_ele = ele.split('_')
        voice_list.append('{} - {}'.format(new_ele[0], new_ele[1]))

    return "\n".join(voice_list).join(['\n', '\n'])


### Main functions ###


def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('LeL.')


def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Use: \n'
                              '- /newvoice to create a new voice file.\n'
                              '- /voice <name> to send the voice file named <name>.\n'
                              '- /listvoices to show saved voices.\n'
                              '- /cancel to cancel the current task.\n')


def start_newvoice(bot, update):
    """Send a message when the command /newvoice is issued."""
    update.message.reply_text(
        'Hi! My name is Siddy Bot. I will hold a conversation with you. LeL.\n'
        'Send /cancel to stop talking to me.\n\n'
        'How would you like to name the voice? LeL.')
    return NAME


def name_voice(bot, update, user_data):
    """Get the name of the voice to be saved"""
    username = update.message.from_user.first_name
    voice_name = update.message.text.lower()

    if glob.glob('voice_files/{file_name}*.ogg'.format(file_name=voice_name)):
        update.message.reply_text(
            'The name {voice_name} is already taken. Please select a different name. LeL.'.format(voice_name=voice_name))
    else:
        user_data['voice_name'] = voice_name
        # print(user_data['voice_name'])
        update.message.reply_text('Okay {username}. LeL.\n'
                                  'The file will be named: {voice_name}\n'
                                  'Now just send a voice message which should be saved! LeL.'.format(username=username,
                                                                                                     voice_name=voice_name))

    return VOICE


def get_voice(bot, update, user_data):
    """Get the voice file from Telegram servers"""
    user = update.message.from_user
    voice_name = user_data['voice_name']
    # print(update.message.voice)
    # print(voice_name)
    file_id = update.message.voice.file_id
    new_file = bot.get_file(file_id)
    new_file.download(
        'voice_files/{voice_name}_{username}_{file_id}.ogg'.format(voice_name=voice_name, username=user.username, file_id=file_id))
    # 'voice_files/cemck.ogg')
    logger.info("Saved voice of %s and named voice file %s. LeL.",
                user.first_name, voice_name)
    update.message.reply_text(
        'Thank you, the voice is now saved as {voice_name}.\n'
        'Use /voice <name> to get the voice!\n'
        'I hope we can talk again some day. LeL.\n'.format(voice_name=voice_name))

    return ConversationHandler.END


def load_voice(bot, update, args):
    """Sends the voice to user"""
    chat_id = update.message.chat_id
    file_name = None
    try:
        file_name = args[0].lower()
        # print(file_name)
    except Exception as err:
        # print(err)
        return update.message.reply_text('Please input the voice name.\n'
                                         'Use /voice <name> to get the voice!\n'
                                         'LeL.')
    try:
        recommended_file = glob.glob(
            'voice_files/{file_name}_*.ogg'.format(file_name=file_name))
        # print('recommeneded_file: {}', recommended_file)

        file_str = recommended_file[0]
        # print('file_str: {}', file_str)

        with open(file_str, 'rb') as voice_file:
            # print('file_str: {}', file_str)
            bot.send_voice(chat_id=chat_id, voice=voice_file)
    except Exception as err:
        # print('load_voice ERROR:\n')
        # print(err)
        update.message.reply_text(
            'Sorry! Could not find voice file named: "{file_name}". LeL.'.format(file_name=file_name))


def list_voices(bot, update):
    files = os.listdir('voice_files')
    # print(files)
    update.message.reply_text('These voices are saved:\n'
                              '{}\n'
                              'LeL.'.format(voice_files_to_str(files)))


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.')

    return ConversationHandler.END


def cancel_blank(bot, update):
    update.message.reply_text('Nothing to cancel here. LeL.')


def main():
    if not os.path.isdir('voice_files'):
        os.mkdir('voice_files')
    # Create the Updater and pass it your bot's token.
    updater = Updater(read_token_from_config_file('config.cfg'))

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("voice", load_voice, pass_args=True))
    dp.add_handler(CommandHandler('listvoices', list_voices))

    # Add conversation handler with the states VOICE, NAME
    conv_handler_newvoice = ConversationHandler(
        entry_points=[CommandHandler('newvoice', start_newvoice)],

        states={
            NAME: [MessageHandler(Filters.text, name_voice, pass_user_data=True)],

            VOICE: [MessageHandler(
                Filters.voice, get_voice, pass_user_data=True)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler_newvoice)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    print('Bot is running...')

    # Block until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
