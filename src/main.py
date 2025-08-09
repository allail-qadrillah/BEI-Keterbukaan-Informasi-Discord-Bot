"""
Main application logic for IDX Discord Bot
Single request fetch -> filter per KEYWORD -> send
"""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import pytz
import json

from config import Config
from api_client import IDXAPIClient
from message_parser import MessageParser, AnnouncementMessage
from discord_handler import DiscordHandler
from database_handler import DatabaseHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class IDXDiscordBot:
    """Main application class for IDX Discord Bot"""

    def __init__(self):
        self.config = Config()
        # Create API client. Mode and rapidapi_config can be changed in env/config
        rapidapi_cfg = getattr(self.config, "RAPIDAPI_CONFIG", None)
        self.api_client = IDXAPIClient(
            base_url=self.config.IDX_API_URL,
            mode=getattr(self.config, "IDX_FETCH_MODE", "direct"),
            proxy=self.config.PROXY,
            rapidapi_config=rapidapi_cfg,
        )
        self.message_parser = MessageParser()

        # Initialize database handler
        self.database_handler = DatabaseHandler(
            supabase_url=self.config.SUPABASE_URL, supabase_key=self.config.SUPABASE_KEY
        )

        # Initialize Discord handler with database dependency
        self.discord_handler = DiscordHandler(
            token=self.config.DISCORD_TOKEN,
            guild_id=self.config.GUILD_ID,
            channel_mapping=self.config.CHANNEL_MAPPING,
            database_handler=self.database_handler,
        )

        self.error_403_state = False  # track if 403 occurred previously

    async def process_filtered_announcements(self, keyword: str, filtered_announcements: List[Dict]) -> int:
        """
        Send messages for the already filtered announcements (so API isn't called per keyword).
        Returns number of messages sent.
        """
        messages_sent = 0

        # sort by CreatedDate ascending (oldest -> newest)
        sorted_announcements = sorted(
            filtered_announcements, key=lambda x: x.get("pengumuman", {}).get("CreatedDate", "")
        )

        for ann in sorted_announcements:
            parsed = self.message_parser.parse_announcement(ann)
            if not parsed:
                continue
            message_content = self.message_parser.format_message(parsed)

            success = await self.discord_handler.send_message(
                keyword=keyword, announcement=parsed, message_content=message_content
            )
            if success:
                messages_sent += 1
                await asyncio.sleep(1)

        logger.info("Sent %s messages for keyword %s", messages_sent, keyword)
        return messages_sent

    async def run(self) -> Dict[str, int]:
        """
        Run the main bot process:
         1) start discord bot
         2) fetch all announcements once
         3) filter per keyword and send
        """
        logger.info("Starting IDX Discord Bot")
        results: Dict[str, int] = {}

        try:
            # Start Discord bot
            await self.discord_handler.start_bot()

            # Fetch announcements once in Jakarta Timezone
            today_str = datetime.now(pytz.timezone("Asia/Jakarta")).strftime("%Y%m%d")
            yesterday_str = (datetime.now(pytz.timezone("Asia/Jakarta")) - timedelta(days=2)).strftime("%Y%m%d")
            # You can change dateFrom in Config or pass as needed; here we keep default in client if None
            api_data, status = self.api_client.fetch_all_announcements(
                date_from=yesterday_str,
                date_to=today_str
            )

            if status == 403:
                # Cloudflare bypass failed
                await self.discord_handler.send_error_message(
                    channel="Error",
                    error_message=f"Cannot Bypass Cloudflare when getting announcements: Status Code 403",
                )
                logger.error("Cannot bypass Cloudflare (403)")
                return results

            if status != 200 or not api_data:
                await self.discord_handler.send_error_message(
                    channel="Error",
                    error_message=f"Failed to fetch announcements: status {status}",
                )
                logger.error("Failed to fetch announcements: status %s", status)
                return results

            # Check method scrapping
            if self.api_client.mode == "rapidapi":
                api_data = json.loads(api_data['data']['body']) # Adjust to the RapidAPI data structure used.

            replies = api_data.get("Replies", [])
            logger.info("Total replies fetched: %s", len(replies))

            # For each keyword, filter locally and process results
            for keyword, keyword_cfg in self.config.KEYWORDS.items():
                try:
                    filtered = self.message_parser.filter_by_keyword(replies, keyword_cfg)
                    count = await self.process_filtered_announcements(keyword, filtered)
                    results[keyword] = count
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.exception("Error processing keyword %s: %s", keyword, e)
                    results[keyword] = 0

            return results

        finally:
            logger.info("Closing Discord connection...")
            await self.discord_handler.close_bot()
            logger.info("Discord connection closed.")


async def main():
    bot = IDXDiscordBot()
    res = await bot.run()
    print("Final results:", res)


if __name__ == "__main__":
    asyncio.run(main())
