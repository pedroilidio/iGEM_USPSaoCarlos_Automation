#!/usr/bin/env python
"""
Telegram bot to fulfill or add references to a reference database in Notion.

Config file must contain:
    telegram_token: Telegram bot's token provided by the BotFather.
    notion_token: (Notion's API integration token).
    references_page_id: the Notion database's ID that can be found in its URL.

Based on:
  https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/echobot.py
"""

import logging, yaml
from functools import partial
from pathlib import Path

from telegram import Update, ForceReply
from telegram.ext import (
    Updater, CommandHandler, MessageHandler,
    Filters, CallbackContext)
from notion_client import Client
from update_references import ReferencesDatabase

SCRIPT_DIR = Path(__file__).parent
CONFIG_PATH = SCRIPT_DIR/"config.yml"

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
    with open(CONFIG_PATH) as config_file:
        config = yaml.safe_load(config_file)

    # Create the Updater and pass it your bot's token.
    updater = Updater(config['telegram_token'])

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command, unknown_command))

    print('Authenticating...', end=' ')
    notion = Client(auth=config['notion_token'])
    references_database = ReferencesDatabase(
        client=notion,
        database_id=config['references_page_id'],
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
