"""
Help command handler for TeraBox Bot
"""
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config_vars import SUPPORT_GROUP, SUPPORT_CHANNEL, HELP_MESSAGE

logger = logging.getLogger(__name__)

class HelpCommand:
    def __init__(self, bot):
        self.bot = bot
        self.bot.on_message(filters.command("help"))(self.handle_help)
    
    async def handle_help(self, client, message: Message):
        """Handle /help command"""
        help_text = HELP_MESSAGE.format(
            support_group=SUPPORT_GROUP,
            support_channel=SUPPORT_CHANNEL
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Back to Main", callback_data="start")],
            [InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP),
             InlineKeyboardButton("📢 Updates", url=SUPPORT_CHANNEL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(help_text, reply_markup=reply_markup)