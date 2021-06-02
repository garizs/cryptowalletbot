from random import choice
import datetime
import logging
import os

import yaml
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, Filters,
                          CallbackQueryHandler)

from api import final_balance, convert_to_money

from money.money import Money
from money.currency import Currency

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %('
                           'message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class Configs:
    def __init__(self):
        configs_path = os.path.join(os.path.dirname(__file__), 'configs.yml')
        with open(configs_path, encoding='utf8') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        self.title = data.get("bot_title", "Bitcoin Bot")
        self.token = data["telegram_token"]
        self.allowed_users = data.get("allowed_user_ids", [])
        self.update_time = data.get("update_each", 3600)
        self.date_frmt = data.get("date_format", "%d/%m/%Y")
        self.hour_frmt = data.get("hour_format", "%H:%M")
        self.money = data["money"]
        self.money_frmt = data["money_format"]
        self.wallets = data['wallets']

        self.str_title = data.get("title", "Bitcoin Bot")
        self.str_wallet_view = data["wallet_view"]
        self.str_fail_wallet_view = data["failed_wallet_view"]
        self.str_extra_content = data.get("extra_content", "")
        self.str_update_button = data.get("update_button", "🔄")

        self.str_placeholder = data["updating"]


def start(update, context):
    configs = Configs()
    update_delay = configs.update_time

    # Send the message with menu
    menu = update.message.reply_text(gui_text(),
                                     reply_markup=buttons(),
                                     parse_mode='Markdown')

    # Updates the display every x minutes
    if len(context.job_queue.jobs()) < 1 and update_delay > 0:
        context.job_queue.run_repeating(bitcoin_refresh_handler,
                                        update_delay,
                                        first=update_delay,
                                        context=menu)


def bitcoin_refresh_handler(context):
    menu = context.job.context
    configs = Configs()

    context.bot.edit_message_text(
        text=choice(configs.str_placeholder),
        chat_id=menu.chat.id,
        message_id=menu.message_id,
        reply_markup=buttons("no_input"),
        parse_mode='Markdown')

    context.bot.edit_message_text(
        text=gui_text(),
        chat_id=menu.chat.id,
        message_id=menu.message_id,
        reply_markup=buttons(),
        parse_mode='Markdown')


def gui_text():
    c = Configs()

    currency = getattr(Currency, c.money)

    update_date = datetime.datetime.now().strftime(c.date_frmt)
    update_hour = datetime.datetime.now().strftime(c.hour_frmt)

    placeholder, one_btc_value = convert_to_money(1, c.money)
    one_btc_value_frmt = Money(str(one_btc_value), currency). \
        format(c.money_frmt)

    start_replacements = {"title": c.title,
                          "update_date": update_date,
                          "update_time": update_hour,
                          "btc_value": one_btc_value_frmt,
                          "currency": c.money}

    txt = ["\n".join(c.str_title).format(**start_replacements)]

    for wallet in c.wallets:
        wallet_name = wallet["name"]
        wallet_addr = wallet['address']
        balance_btc = final_balance(wallet_addr)
        if balance_btc is not None:
            balance_money, btc_value = convert_to_money(balance_btc,
                                                        c.money)
            balance_money = Money(str(balance_money),
                                  currency).format(c.money_frmt)

            wallet_replacements = {"btc_balance": balance_btc,
                                   "money_balance": balance_money,
                                   "wallet": wallet_name,
                                   "wallet_address": wallet_addr}

            txt.append("\n".join(c.str_wallet_view).
                       format(**wallet_replacements, **start_replacements))
        else:
            wallet_replacements = {"wallet": wallet_name,
                                   "wallet_address": wallet_addr}

            txt.append("\n".join(c.str_fail_wallet_view).
                       format(**wallet_replacements, **start_replacements))

    txt.append("\n".join(c.str_extra_content).format(**start_replacements))

    return ''.join(txt)


def buttons(tipo: str = 'main'):
    configs = Configs()

    keyboard = []
    if tipo == 'main':
        keyboard = [
            [InlineKeyboardButton(configs.str_update_button,
                                  callback_data='update'), ],
        ]

    elif tipo == 'no_input':
        keyboard = [
            [InlineKeyboardButton(configs.str_update_button,
                                  callback_data='update'), ],
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


def answer_handler(update, context):
    query = update.callback_query.data

    configs = Configs()

    if query == 'update':
        context.bot.edit_message_text(
            text=choice(configs.str_placeholder),
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=buttons('no_input'),
            parse_mode='Markdown')

        context.bot.edit_message_text(
            text=gui_text(),
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id,
            reply_markup=buttons(),
            parse_mode='Markdown')


def error_callback(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    configs = Configs()

    updater = Updater(configs.token, use_context=True)

    updater.dispatcher.add_handler(
        CommandHandler('start', start,
                       Filters.user(configs.allowed_users, allow_empty=True)))
    updater.dispatcher.add_handler(CallbackQueryHandler(answer_handler))
    updater.dispatcher.add_error_handler(error_callback)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
