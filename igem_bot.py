#!/usr/bin/env python
"""
Simple Bot to reply to Telegram messages.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

Based on:
  https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py
"""

import logging
from functools import partial

from telegram import Update, ForceReply
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    Filters, CallbackContext)
from notion_client import Client
from update_references import ReferencesDatabase

REFERENCES_PAGE_ID = '610b6086600f45d48065b7a46eb1e8bd'
TELEGRAM_TOKEN_PATH = 'TELEGRAM_TOKEN.txt'
NOTION_TOKEN_PATH = 'NOTION_TOKEN.txt'

with open(TELEGRAM_TOKEN_PATH) as token_file:
    TELEGRAM_TOKEN = token_file.read().strip()
with open(NOTION_TOKEN_PATH) as token_file:
    NOTION_TOKEN = token_file.read().strip()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )
    help_command(update, context)


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help not ready yet!')


def unknown_command(update: Update, context: CallbackContext) -> None:
    """Deals with an unknown input by the user."""
    update.message.reply_text(f"I didn't understand what you want.")
    help_command(update, context)


def add_references(
        update: Update,
        context: CallbackContext,
        references_database: ReferencesDatabase) -> None:
    """Add references to the database."""
    doilist = update.message.text.split()[1:]
    update.message.reply_text(
        "Adding the following references to the database:\n* " +
        '\n* '.join(doilist)
    )
    references_database.add_references(doilist)


def fill_incomplete_references(
        update: Update,
        context: CallbackContext,
        references_database: ReferencesDatabase) -> None:
    """Fetch and fill metadata of all references with DOI but no name."""
    update.message.reply_text('Fulfilling DOI-only references...')
    references_database.fullfil_doi_only()


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(TELEGRAM_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, unknown_command))

    print('Authenticating...', end=' ')
    notion = Client(auth=NOTION_TOKEN)
    references_database = ReferencesDatabase(
        client=notion,
        database_id=REFERENCES_PAGE_ID,
    )
    print('Done.')

    dispatcher.add_handler(CommandHandler(
        "fill_incomplete_references",
        partial(fill_incomplete_references,
                references_database=references_database)
    ))
    dispatcher.add_handler(CommandHandler(
        "add_references",
        partial(add_references, references_database=references_database)
    ))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
