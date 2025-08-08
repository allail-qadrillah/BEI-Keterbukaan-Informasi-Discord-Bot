"""
Discord bot handler for sending messages
"""

import discord
import logging
import asyncio
from typing import Dict, List, Optional
from discord.ext import commands
from message_parser import AnnouncementMessage
from database_handler import DatabaseHandler

logger = logging.getLogger(__name__)


class DiscordHandler:
    """Handler for Discord bot operations"""

    def __init__(
        self,
        token: str,
        guild_id: str,
        channel_mapping: Dict[str, str],
        database_handler: DatabaseHandler,
    ):
        """
        Initialize Discord handler

        Args:
            token: Discord bot token
            guild_id: Discord guild ID
            channel_mapping: Mapping of keywords to channel names
            database_handler: Database handler instance
        """
        self.token = token
        self.guild_id = int(guild_id) if guild_id else None
        self.channel_mapping = channel_mapping
        self.database_handler = database_handler
        self.bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
        self.is_ready = False
        self._ready_event = asyncio.Event()

        @self.bot.event
        async def on_ready():
            logger.info(f"Bot logged in as {self.bot.user}")
            self.is_ready = True
            self._ready_event.set()  # Signal that bot is ready

    async def start_bot(self):
        """Start the Discord bot"""
        try:
            # Start the bot in the background
            self._bot_task = asyncio.create_task(self.bot.start(self.token))

            # Wait for the bot to be ready
            await self._ready_event.wait()
            logger.info("Bot is ready for operations")

        except Exception as e:
            logger.error(f"Failed to start bot: {str(e)}")
            raise

    async def close_bot(self):
        """Close the Discord bot connection"""
        if hasattr(self, "_bot_task"):
            self._bot_task.cancel()
            try:
                await self._bot_task
            except asyncio.CancelledError:
                pass

        if self.bot:
            await self.bot.close()

    async def get_channel(self, keyword: str) -> Optional[discord.TextChannel]:
        """
        Get Discord channel for specific keyword

        Args:
            keyword: Keyword to find channel for

        Returns:
            Discord channel or None if not found
        """
        if not self.is_ready:
            logger.error("Bot is not ready yet")
            return None

        channel_name = self.channel_mapping.get(keyword)
        if not channel_name:
            logger.error(f"No channel mapping for keyword: {keyword}")
            return None

        guild = self.bot.get_guild(self.guild_id)
        if not guild:
            logger.error(f"Guild not found: {self.guild_id}")
            return None

        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if not channel:
            logger.error(f"Channel not found: {channel_name}")
            return None

        return channel

    async def send_message(
        self,
        keyword: str,
        announcement: AnnouncementMessage,
        message_content: str,
        check_duplicate: bool = True,
    ) -> bool:
        """
        Send message to appropriate channel with database duplicate checking

        Args:
            keyword: Keyword to determine channel
            announcement: Parsed announcement data
            message_content: Message to send
            check_duplicate: Whether to check for duplicate messages

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if not self.is_ready:
                logger.error("Bot is not ready to send messages")
                return False

            channel = await self.get_channel(keyword)
            if not channel:
                return False

            # Check for duplicate in database
            if check_duplicate:
                exists = await self.database_handler.message_exists(
                    announcement.kode_emiten,
                    announcement.judul_pengumuman,
                    message_content,
                    announcement.created_date,
                )

                if exists:
                    logger.info(
                        f"Skipping duplicate message for {announcement.kode_emiten}: {announcement.judul_pengumuman}"
                    )
                    return True

            # Send message to Discord
            await channel.send(message_content)
            logger.info(f"Message sent to channel: {channel.name}")

            # Save message to database
            save_success = await self.database_handler.save_message(
                kode_emiten=announcement.kode_emiten,
                judul=announcement.judul_pengumuman,
                channel_name=channel.name,
                message_content=message_content,
                created_date=announcement.created_date,
            )

            if not save_success:
                logger.warning(
                    f"Message sent but failed to save to database for {announcement.kode_emiten}"
                )

            return True

        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return False

    async def send_error_message(self, channel: str, error_message: str) -> bool:
        """
        Send error message to appropriate channel

        Args:
            channel: Channel name to send the error message
            error_message: Error message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if not self.is_ready:
                logger.error("Bot is not ready to send error messages")
                return False
            print(f"Sending error message to channel: {channel}")
            channel = await self.get_channel(channel)
            print(f"Channel found: {channel}")
            
            await channel.send(f"**Error:** {error_message}")
            logger.error(f"Error message sent to channel: {channel.name}")
            return True

        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}")
            return False
