"""
TeraBox Bot - Main Entry Point
Supports both FastAPI web server and Telegram bot
"""
import os
import asyncio
import logging
from threading import Thread
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pyrogram import Client
from commands.start import StartCommand
from commands.help import HelpCommand
from commands.stream import StreamCommand
from mongodb_config import init_mongodb

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="TeraBox Bot API", version="1.0.0")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7642271614:AAE65-0CW1g4hhXk2yM719kUHxle6TkCiUk")
API_ID = int(os.getenv("API_ID", "12380656"))
API_HASH = os.getenv("API_HASH", "be63383612b8f4eb0c65e88a7a49b2b8")
LOG_GROUP_ID = int(os.getenv("LOG_GROUP_ID", "-1002469952747"))

# Initialize Pyrogram client
bot = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Command handlers
start_handler = StartCommand(bot)
help_handler = HelpCommand(bot)
stream_handler = StreamCommand(bot)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await init_mongodb()
    logger.info("MongoDB initialized")
    
    # Start bot in background
    asyncio.create_task(start_bot())
    logger.info("TeraBox Bot started")

async def start_bot():
    """Start the Telegram bot"""
    try:
        await bot.start()
        
        # Send startup message to log group
        try:
            await bot.send_message(
                LOG_GROUP_ID,
                "🤖 **TeraBox Bot Started Successfully!**\n\n"
                "✅ Bot is now online and ready to process TeraBox links.\n"
                "📊 Monitoring all activities."
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
        
        logger.info("TeraBox Bot started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/stream/{video_id}")
async def stream_video(video_id: str, request: Request):
    """Stream video page"""
    from features.stream import get_video_by_id
    
    try:
        video = await get_video_by_id(video_id)
        if not video:
            return JSONResponse({"error": "Video not found"}, status_code=404)
        
        return templates.TemplateResponse("stream.html", {
            "request": request,
            "video": video
        })
    except Exception as e:
        logger.error(f"Error streaming video {video_id}: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@app.get("/api/video/{video_id}")
async def get_video_info(video_id: str):
    """Get video information as JSON"""
    from features.info import get_video_details
    
    try:
        video_data = await get_video_details(video_id)
        if not video_data:
            return JSONResponse({"error": "Video not found"}, status_code=404)
        
        return JSONResponse(video_data)
    except Exception as e:
        logger.error(f"Error getting video info {video_id}: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@app.get("/download/{video_id}")
async def download_video(video_id: str):
    """Download video redirect"""
    from features.download import get_download_url
    
    try:
        download_url = await get_download_url(video_id)
        if not download_url:
            return JSONResponse({"error": "Download not available"}, status_code=404)
        
        return JSONResponse({"download_url": download_url})
    except Exception as e:
        logger.error(f"Error downloading video {video_id}: {e}")
        return JSONResponse({"error": "Internal server error"}, status_code=500)

@app.get("/stats")
async def get_stats():
    """Get bot statistics"""
    from mongodb_config import videos_sync, downloads_sync
    
    try:
        total_videos = videos_sync.count_documents({})
        total_streams = downloads_sync.count_documents({"download_type": "stream"})
        total_downloads = downloads_sync.count_documents({"download_type": "download"})
        
        return JSONResponse({
            "total_videos": total_videos,
            "total_streams": total_streams,
            "total_downloads": total_downloads
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return JSONResponse({
            "total_videos": 0,
            "total_streams": 0,
            "total_downloads": 0
        })

if __name__ == "__main__":
    # Run with uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)