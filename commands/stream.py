"""
Stream/Download command handler for TeraBox Bot
"""
import logging
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from terabox_scraper import TeraBoxScraper
from utils import validate_terabox_url, format_file_size
from mongodb_config import MongoVideo
from features.info import format_duration
from config_vars import LOG_GROUP_ID, SUPPORT_GROUP, SUPPORT_CHANNEL, START_MESSAGE, HELP_MESSAGE

logger = logging.getLogger(__name__)

class StreamCommand:
    def __init__(self, bot):
        self.bot = bot
        self.scraper = TeraBoxScraper()
        
        # Register handlers
        self.bot.on_message(filters.text & filters.private & ~filters.command(["start", "help", "history"]))(self.handle_message)
        self.bot.on_callback_query()(self.handle_callback)
    
    async def handle_message(self, client, message: Message):
        """Handle incoming messages with TeraBox links"""
        message_text = message.text
        user_id = message.from_user.id
        
        # Check if message contains TeraBox link
        if not validate_terabox_url(message_text):
            await message.reply_text(
                "❌ Please send a valid TeraBox link.\n\n"
                f"📖 Need help? Use /help\n"
                f"👥 Support: {SUPPORT_GROUP}"
            )
            return
        
        terabox_url = message_text.strip()
        
        # Show processing message
        processing_msg = await message.reply_text("🔄 Processing your TeraBox link...\n\nPlease wait while I extract video information.")
        
        try:
            # Extract video information
            video_info = await self.scraper.extract_video_info(terabox_url)
            
            if not video_info:
                await processing_msg.edit_text("❌ Failed to extract video information. Please check the link and try again.")
                return
            
            # Save to MongoDB
            try:
                video_data = {
                    "user_id": user_id,
                    "original_url": terabox_url,
                    "title": video_info.get('title', 'Unknown Title'),
                    "file_size": video_info.get('file_size', 0),
                    "duration": video_info.get('duration', 0),
                    "thumbnail_url": video_info.get('thumbnail_url'),
                    "video_url": video_info.get('video_url'),
                    "download_urls": video_info.get('download_urls', []),
                    "status": 'completed'
                }
                video_id = await MongoVideo.create(video_data)
                
                # Log to log group
                try:
                    await self.bot.send_message(
                        LOG_GROUP_ID,
                        f"📹 **New Video Processed**\n\n"
                        f"👤 User: {message.from_user.first_name} (`{user_id}`)\n"
                        f"🎬 Title: {video_info.get('title', 'Unknown')}\n"
                        f"📏 Size: {format_file_size(video_info.get('file_size', 0))}\n"
                        f"🔗 URL: `{terabox_url[:50]}...`"
                    )
                except Exception as e:
                    logger.error(f"Failed to log video processing: {e}")
                    
            except Exception as e:
                logger.error(f"Database error: {e}")
                video_id = None
            
            # Create response message
            response_text = f"✅ **Video Processing Complete!**\n\n"
            response_text += f"📺 **Title:** {video_info.get('title', 'Unknown Title')}\n"
            response_text += f"📏 **Size:** {format_file_size(video_info.get('file_size', 0))}\n"
            response_text += f"⏱️ **Duration:** {format_duration(video_info.get('duration', 0))}\n\n"
            response_text += "What would you like to do?"
            
            keyboard = [
                [InlineKeyboardButton("🎥 Stream Online", callback_data=f"stream_{video_id}")],
                [InlineKeyboardButton("📥 Download", callback_data=f"download_{video_id}")],
                [InlineKeyboardButton("ℹ️ More Info", callback_data=f"info_{video_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_msg.edit_text(response_text, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Error processing TeraBox URL: {e}")
            await processing_msg.edit_text("❌ An error occurred while processing your link. Please try again later.")
    
    async def handle_callback(self, client, callback_query: CallbackQuery):
        """Handle callback queries from inline keyboards"""
        await callback_query.answer()
        
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if data == "help":
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
            await callback_query.edit_message_text(help_text, reply_markup=reply_markup)
            
        elif data == "history":
            await self.handle_history(callback_query)
            
        elif data == "start":
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
            await callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
            
        elif data.startswith("stream_"):
            video_id = data.split("_")[1]
            await self.handle_stream_request(callback_query, video_id, user_id)
        elif data.startswith("download_"):
            video_id = data.split("_")[1]
            await self.handle_download_request(callback_query, video_id, user_id)
        elif data.startswith("info_"):
            video_id = data.split("_")[1]
            await self.handle_info_request(callback_query, video_id, user_id)
    
    async def handle_history(self, callback_query):
        """Handle history request"""
        user_id = callback_query.from_user.id
        
        try:
            recent_videos = await MongoVideo.find_by_user(user_id, limit=10)
            
            if not recent_videos:
                await callback_query.edit_message_text("📝 No recent links found. Send me a TeraBox link to get started!")
                return
            
            history_message = "📚 **Your Recent Links:**\n\n"
            for i, video in enumerate(recent_videos, 1):
                status_emoji = "✅" if video.get("status") == "completed" else "⏳" if video.get("status") == "processing" else "❌"
                title = video.get("title", "Unknown Title")
                created_at = video.get("created_at")
                date_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at else "Unknown"
                history_message += f"{i}. {status_emoji} {title}\n"
                history_message += f"   📅 {date_str}\n\n"
            
            await callback_query.edit_message_text(history_message)
        except Exception as e:
            logger.error(f"Database error: {e}")
            await callback_query.edit_message_text("📝 No recent links found. Send me a TeraBox link to get started!")
    
    async def handle_stream_request(self, callback_query, video_id, user_id):
        """Handle stream request"""
        try:
            video = await MongoVideo.find_by_id(video_id)
            
            if not video or video.get("user_id") != user_id:
                await callback_query.edit_message_text("❌ Video not found or access denied.")
                return
        
            # Generate streaming URL
            stream_url = f"https://your-domain.com/stream/{video_id}"
            
            response_text = f"🎥 **Streaming Ready!**\n\n"
            response_text += f"📺 **{video.get('title')}**\n"
            response_text += f"📏 Size: {format_file_size(video.get('file_size', 0))}\n\n"
            response_text += f"🌐 **Stream URL:** [Click to Watch]({stream_url})\n\n"
            response_text += "💡 **Tips:**\n"
            response_text += "• Works best on mobile browsers\n"
            response_text += "• Supports fullscreen playback\n"
            response_text += "• No download required"
        
            keyboard = [
                [InlineKeyboardButton("🎬 Open Player", url=stream_url)],
                [InlineKeyboardButton("📥 Download Instead", callback_data=f"download_{video_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"info_{video_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await callback_query.edit_message_text(response_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Database error: {e}")
            await callback_query.edit_message_text("❌ Error accessing video data.")
    
    async def handle_download_request(self, callback_query, video_id, user_id):
        """Handle download request"""
        try:
            video = await MongoVideo.find_by_id(video_id)
            
            if not video or video.get("user_id") != user_id:
                await callback_query.edit_message_text("❌ Video not found or access denied.")
                return
        
            response_text = f"📥 **Download Options**\n\n"
            response_text += f"📺 **{video.get('title')}**\n"
            response_text += f"📏 Size: {format_file_size(video.get('file_size', 0))}\n\n"
            response_text += "Choose your preferred download link:\n\n"
            
            # Create download buttons
            keyboard = []
            download_urls = video.get('download_urls', [])
            
            if isinstance(download_urls, str):
                import json
                try:
                    download_urls = json.loads(download_urls)
                except:
                    download_urls = [download_urls]
        
            for i, url in enumerate(download_urls[:3], 1):  # Limit to 3 download options
                keyboard.append([InlineKeyboardButton(f"📥 Download Link {i}", url=url)])
            
            keyboard.extend([
                [InlineKeyboardButton("🎥 Stream Instead", callback_data=f"stream_{video_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data=f"info_{video_id}")]
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await callback_query.edit_message_text(response_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Database error: {e}")
            await callback_query.edit_message_text("❌ Error accessing video data.")
    
    async def handle_info_request(self, callback_query, video_id, user_id):
        """Handle info request"""
        try:
            video = await MongoVideo.find_by_id(video_id)
            
            if not video or video.get("user_id") != user_id:
                await callback_query.edit_message_text("❌ Video not found or access denied.")
                return
        
            response_text = f"ℹ️ **Video Information**\n\n"
            response_text += f"📺 **Title:** {video.get('title')}\n"
            response_text += f"📏 **Size:** {format_file_size(video.get('file_size', 0))}\n"
            response_text += f"⏱️ **Duration:** {format_duration(video.get('duration', 0))}\n"
            created_at = video.get('created_at')
            date_str = created_at.strftime('%Y-%m-%d %H:%M') if created_at else "Unknown"
            response_text += f"📅 **Added:** {date_str}\n"
            response_text += f"🔗 **Original Link:** [TeraBox]({video.get('original_url')})\n\n"
            response_text += "What would you like to do?"
        
            keyboard = [
                [InlineKeyboardButton("🎥 Stream Online", callback_data=f"stream_{video_id}")],
                [InlineKeyboardButton("📥 Download", callback_data=f"download_{video_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await callback_query.edit_message_text(response_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Database error: {e}")
            await callback_query.edit_message_text("❌ Error accessing video data.")