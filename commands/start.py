"""
Start command handler for TeraBox Bot
"""
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from mongodb_config import MongoUser
from config_vars import LOG_GROUP_ID, SUPPORT_GROUP, SUPPORT_CHANNEL, START_MESSAGE

logger = logging.getLogger(__name__)

class StartCommand:
    def __init__(self, bot):
        self.bot = bot
        self.bot.on_message(filters.command("start"))(self.handle_start)
    
    async def handle_start(self, client, message: Message):
        """Handle /start command"""
        user = message.from_user
        
        # Save user to MongoDB
        try:
            user_data = {
                "telegram_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": True
            }
            await MongoUser.create_or_update(user_data)
            
            # Log new user to log group
            try:
                await self.bot.send_message(
                    LOG_GROUP_ID,
                    f"👤 **New User Started Bot**\n\n"
                    f"🆔 ID: `{user.id}`\n"
                    f"👤 Name: {user.first_name} {user.last_name or ''}\n"
                    f"🔗 Username: @{user.username or 'None'}"
                )
            except Exception as e:
                logger.error(f"Failed to log new user: {e}")
                
        except Exception as e:
            logger.error(f"Database error: {e}")
        
        welcome_text = START_MESSAGE.format(
            support_group=SUPPORT_GROUP,
            support_channel=SUPPORT_CHANNEL
        )
        
        keyboard = [
            [InlineKeyboardButton("📖 Help", callback_data="help"),
             InlineKeyboardButton("📊 History", callback_data="history")],
            [InlineKeyboardButton("👥 Support Group", url=SUPPORT_GROUP),
             InlineKeyboardButton("📢 Updates", url=SUPPORT_CHANNEL)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(welcome_text, reply_markup=reply_markup)