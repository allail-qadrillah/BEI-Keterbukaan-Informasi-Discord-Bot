"""
Main application logic for IDX Discord Bot
"""
import asyncio
import logging
from typing import Dict, List
from config import Config
from api_client import IDXAPIClient
from message_parser import MessageParser
from discord_handler import DiscordHandler
from database_handler import DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IDXDiscordBot:
    """Main application class for IDX Discord Bot"""
    
    def __init__(self):
        """Initialize the bot with configuration"""
        self.config = Config()
        self.api_client = IDXAPIClient(
            base_url=self.config.IDX_API_URL,
            # proxy=self.config.PROXY if hasattr(self.config, 'PROXY') else None
        )
        self.message_parser = MessageParser()
        
        # Initialize database handler
        self.database_handler = DatabaseHandler(
            supabase_url=self.config.SUPABASE_URL,
            supabase_key=self.config.SUPABASE_KEY
        )
        
        # Initialize Discord handler with database dependency
        self.discord_handler = DiscordHandler(
            token=self.config.DISCORD_TOKEN,
            guild_id=self.config.GUILD_ID,
            channel_mapping=self.config.CHANNEL_MAPPING,
            database_handler=self.database_handler
        )
        self.error_403_state = False  # Track 403 error state
    
    async def process_keyword(self, keyword: str, keyword_config) -> int:
        """
        Process announcements for a specific keyword
        
        Args:
            keyword: Keyword to search for
            keyword_config: Configuration for the keyword
            
        Returns:
            Number of messages sent
        """
        logger.info(f"Processing keyword: {keyword}")
        
        # Fetch data from API
        api_data, status_code = self.api_client.fetch_announcements(keyword)

        if status_code == 403 and self.error_403_state == False:
            await self.discord_handler.send_error_message(
                channel="Error",
                error_message=f"Cannot Bypass Cloudflare when get {keyword}: Status Code 403"
            )
            self.error_403_state = True
            logger.error(f"Cannot bypass Cloudflare for keyword: {keyword}")
            return 0
        elif status_code != 200:
            await self.discord_handler.send_error_message(
                channel="Error",
                error_message=f"Failed to fetch data for {keyword}: Status Code {status_code}"
            )
            logger.error(f"Failed to fetch data for keyword: {keyword} with status code {status_code}")
            return 0

        if not api_data or 'Replies' not in api_data:
            logger.warning(f"No data received for keyword: {keyword}")
            return 0
        
        # Filter announcements
        announcements = api_data['Replies']
        # sort announcement from first order to last order
        filtered_announcements = sorted(announcements, key=lambda x: x['pengumuman']['CreatedDate'], reverse=False)
        if not filtered_announcements:
            logger.info(f"No matching announcements for keyword: {keyword}")
            return 0
        
        # Process and send messages
        messages_sent = 0
        for announcement_data in filtered_announcements:
            filtered_announcements = self.message_parser.filter_by_keyword(
                [announcement_data], 
                keyword_config
            )
            parsed_announcement = self.message_parser.parse_announcement(announcement_data)
            if parsed_announcement:
                message_content = self.message_parser.format_message(parsed_announcement)
                
                success = await self.discord_handler.send_message(
                    keyword=keyword, 
                    announcement=parsed_announcement,
                    message_content=message_content
                )

                if success:
                    messages_sent += 1
                    # Add small delay between messages
                    await asyncio.sleep(1)
        
        logger.info(f"Sent {messages_sent} messages for keyword: {keyword}")
        return messages_sent
    
    async def run(self) -> Dict[str, int]:
        """
        Run the main bot process
        
        Returns:
            Dictionary with results for each keyword
        """
        logger.info("Starting IDX Discord Bot")
        results = {}
        
        try:
            # Start Discord bot
            await self.discord_handler.start_bot()
            
            # Optional: Clean up old messages (uncomment if needed)
            # await self.database_handler.cleanup_old_messages(days=30)
            
            # Process each keyword
            for keyword, keyword_config in self.config.KEYWORDS.items():
                try:
                    count = await self.process_keyword(keyword, keyword_config)
                    results[keyword] = count
                    # Add small delay between keyword processing
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error processing keyword {keyword}: {str(e)}")
                    results[keyword] = 0
            
            logger.info(f"Bot run completed. Results: {results}")
            return results
        
        except Exception as e:
            logger.error(f"Fatal error in bot execution: {str(e)}")
            raise
        
        finally:
            # Close Discord bot
            logger.info("Closing Discord connection...")
            await self.discord_handler.close_bot()
            logger.info("Discord connection closed.")

async def main():
    """Main entry point"""
    try:
        bot = IDXDiscordBot()
        results = await bot.run()
        print(f"Final results: {results}")
        return results
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())