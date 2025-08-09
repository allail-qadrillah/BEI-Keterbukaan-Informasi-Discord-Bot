"""
Database handler for Supabase operations
"""
from __future__ import annotations

import logging
import hashlib
from typing import Optional, Dict, Any
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """Handler for Supabase database operations"""

    def __init__(self, supabase_url: str, supabase_key: str) -> None:
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize Supabase client: %s", e)
            raise

    def _generate_message_hash(self, kode_emiten: str, judul: str, message_content: str, created_date: str) -> str:
        message_key = f"{kode_emiten.strip().upper()}|{judul.strip()}|{message_content.strip()}|{created_date.strip()}"
        return hashlib.sha256(message_key.encode("utf-8")).hexdigest()

    async def message_exists(self, kode_emiten: str, judul: str, message_content: str, created_date: str) -> bool:
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False

            message_hash = self._generate_message_hash(kode_emiten, judul, message_content, created_date)
            result = self.client.table("sent_messages").select("id").eq("message_hash", message_hash).execute()
            exists = bool(result.data)
            if exists:
                logger.info("Duplicate message found for %s: %s", kode_emiten, judul)
            return exists
        except Exception as e:
            logger.exception("Error checking message existence: %s", e)
            return False

    async def save_message(self, kode_emiten: str, judul: str, channel_name: str, message_content: str, created_date: str = None) -> bool:
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False

            message_hash = self._generate_message_hash(kode_emiten, judul, message_content, created_date or "")
            message_data = {
                "message_hash": message_hash,
                "kode_emiten": kode_emiten.strip().upper(),
                "judul": judul.strip(),
                "channel_name": channel_name,
                "message_content": message_content,
                "announcement_date": created_date,
                "sent_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            }
            result = self.client.table("sent_messages").insert(message_data).execute()
            if result.data:
                logger.info("Message saved to database for %s", kode_emiten)
                return True
            logger.error("Failed to save message for %s", kode_emiten)
            return False
        except Exception as e:
            logger.exception("Error saving message to database: %s", e)
            return False

    async def cleanup_old_messages(self, days: int = 30) -> int:
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return 0

            cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=days)
            result = self.client.table("sent_messages").delete().lt("sent_at", cutoff.isoformat()).execute()

            deleted_count = len(result.data) if result.data else 0
            logger.info("Cleaned up %s old messages", deleted_count)
            return deleted_count
        except Exception as e:
            logger.exception("Error cleaning up old messages: %s", e)
            return 0
