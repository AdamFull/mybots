import threading, logging, html, traceback, json
from telegram import Update, ForceReply, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, Handler
from configuration import Configuration
from net_checker import NetChecker
from session_instance import SessionInstance

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

def GenerateCBLinks(names: list) -> str:
    links: str = ""
    for name in names:
        links += f"https://chaturbate.com/{name}\n"
    return links

def CheckArguments(args: str, min: int, max: int, update: Update) -> bool:
    if len(args) > max:
        update.message.reply_text("Too match arguments.")
        return False
    elif len(args) <= min:
        update.message.reply_text("Too few arguments.")
        return False
    return True

class RestrictHandler(Handler):
    def __init__(self):
        super().__init__(self.cb)

    def cb(self, update: Update, context):
        update.message.reply_text('You don\'t have permissions for using this bot.')

    def check_update(self, update: Update):
        if update.message is None or update.message.from_user.id not in Configuration().GetBotWhitelist():
            return True

        return False

class MessagingBot(threading.Thread):

    _last_user = None
    _logger = None
    _old_notification: list = None
    def __init__(self):
        threading.Thread.__init__(self)
        self._logger = logging.getLogger(__name__)

    def run(self):
        updater = Updater(Configuration().GetBotToken())

        dispatcher = updater.dispatcher

        # on different commands - answer in Telegram
        dispatcher.add_handler(RestrictHandler())
        dispatcher.add_handler(CommandHandler("start", self.__start_command))
        dispatcher.add_handler(CommandHandler("help", self.__help_command))
        dispatcher.add_handler(CommandHandler("set_save_dir", self.__set_save_dir_command))
        dispatcher.add_handler(CommandHandler("set_check_interval", self.__set_check_interval_command))
        dispatcher.add_handler(CommandHandler("add_model", self.__add_model_command))
        dispatcher.add_handler(CommandHandler("remove_model", self.__remove_model_command))
        dispatcher.add_handler(CommandHandler("add_gender", self.__add_gender_command))
        dispatcher.add_handler(CommandHandler("remove_gender", self.__remove_gender_command))
        dispatcher.add_handler(CommandHandler("change_auth", self.__change_auth_command))
        dispatcher.add_handler(CommandHandler("model_list", self.__model_list_command))
        dispatcher.add_handler(CommandHandler("recording_now", self.__recording_now_command))

        dispatcher.add_handler(CommandHandler("enable_notification", self.__enable_notification_command))
        dispatcher.add_handler(CommandHandler("disable_notification", self.__disable_notification_command))

        # on non command i.e message - echo the message on Telegram
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, self.__echo))

        dispatcher.add_error_handler(self.__error_handler)

        # Start the Bot
        updater.start_polling()


    def __error_handler(self, update: object, context: CallbackContext) -> None:
        """Log the error and send a telegram message to notify the developer."""
        # Log the error before we do anything else, so we can see it even if something breaks.
        self._logger.error(msg="Exception while handling an update:", exc_info=context.error)

        # traceback.format_exception returns the usual python message about an exception, but as a
        # list of strings rather than a single string, so we have to join them together.
        tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
        tb_string = ''.join(tb_list)

        # Build the message with some markup and additional information about what happened.
        # You might need to add some logic to deal with messages longer than the 4096 character limit.
        update_str = update.to_dict() if isinstance(update, Update) else str(update)
        message = (
            f'An exception was raised while handling an update\n'
            f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
            '</pre>\n\n'
            f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
            f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
            f'<pre>{html.escape(tb_string)}</pre>'
        )
        context.bot.send_message(chat_id=Configuration().GetBotWhitelist()[0], text=message, parse_mode=ParseMode.HTML)

    def __start_command(self, update: Update, context: CallbackContext) -> None:
        self.user = update.effective_user
        self.__enable_notification_command(update, context)
        

    def __help_command(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text('''
        Commands:
        /set_save_dir {path} - set output directory path
        /set_check_interval {time_in_sec} - set check online interval
        /add_model {name} - add model nickname
        /remove_model {name} - remove model nickname
        /add_gender {name} - add gender
        /remove_gender {name} - remove gender
        /change_auth {login} {password} - set new login and password
        /model_list - model links
        /recording_now - model links for now streaming models
        /enable_notification - enable notification about active models
        /disable_notification - disable notifications
        ''')
        

    def __set_save_dir_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().SetSaveDirectory(args[0])
        update.message.reply_text(f"New output path is: {args[0]}")
        
    
    def __set_check_interval_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().SetCheckInterval(int(args[0]))
        update.message.reply_text(f"New update interval is: {args[0]}")
        

    def __add_model_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().AddModel(args[0])
        update.message.reply_text(f"Added new model: {args[0]}")
        

    def __remove_model_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().RemoveModel(args[0])
        update.message.reply_text(f"Removed model: {args[0]}")
        

    def __add_gender_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().AddModel(args[0])
        update.message.reply_text(f"Added new gender: {args[0]}")
        

    def __remove_gender_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 0, 1, update):
            return None

        Configuration().RemoveModel(args[0])
        update.message.reply_text(f"Removed gender: {args[0]}")
        

    def __change_auth_command(self, update: Update, context: CallbackContext) -> None:
        args = context.args
        if not CheckArguments(args, 1, 2, update):
            return None

        Configuration().SetLogin(args[0])
        Configuration().SetPassword(args[1])
        password = ""
        password.join(['*' for i in range(len(args[1]))])
        update.message.reply_text(f"Auth data changed: Login: {args[0]} Password: {password}")
        


    def __model_list_command(self, update: Update, context: CallbackContext) -> None:
        update.message.reply_text(f"Models list: \n {GenerateCBLinks(Configuration().GetModels())}")
        

    def __recording_now_command(self, update: Update, context: CallbackContext) -> None:
        recordings = [n.GetName() for n in SessionInstance().GetRecording()]
        if recordings:
            update.message.reply_text(f"Recording list: \n {GenerateCBLinks()}")
        


    def __notification(self, context: CallbackContext) -> None:
        job = context.job
        online_recordings = [n.GetName() for n in SessionInstance().GetRecording()]
        if len(online_recordings) > 0 and not online_recordings == self._old_notification:
            self._old_notification = online_recordings
            context.bot.send_message(job.context, text=f"Recording list: \n {GenerateCBLinks(online_recordings)}")

    def __remove_job_if_exists(self, name: str, context: CallbackContext) -> bool:
        current_jobs = context.job_queue.get_jobs_by_name(name)
        if not current_jobs:
            return False
        for job in current_jobs:
            job.schedule_removal()
        return True

    def __enable_notification_command(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        try:
            self.__remove_job_if_exists(str(chat_id), context)
            context.job_queue.run_repeating(self.__notification, Configuration().GetBotNotificationPeriod(), context=chat_id, name=str(chat_id))

            text = 'Notification enabled!'
            update.message.reply_text(text)

        except (IndexError, ValueError):
            pass

    def __disable_notification_command(self, update: Update, context: CallbackContext) -> None:
        chat_id = update.message.chat_id
        job_removed = self.__remove_job_if_exists(str(chat_id), context)
        text = 'Notification disabled!' if job_removed else 'You have no active notifications.'
        update.message.reply_text(text)


    def __echo(self, update: Update, context: CallbackContext) -> None:
        pass




def main() -> None:
    bot = MessagingBot()
    bot.run()

if __name__ == '__main__':
    main()

