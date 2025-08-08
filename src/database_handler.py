"""
Database handler for Supabase operations
"""
import logging
import hashlib
from typing import Optional, Dict, Any
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseHandler:
    """Handler for Supabase database operations"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize database handler
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service key
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client"""
        try:
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise

    def _generate_message_hash(self, kode_emiten: str, judul: str, message_content: str, created_date: str) -> str:
        """
        Generate unique hash for message identification
        
        Args:
            kode_emiten: Stock code
            judul: Announcement title
            message_content: Full message content
            created_date: Original announcement date

        Returns:
            SHA-256 hash string
        """
        message_key = f"{kode_emiten.strip().upper()}|{judul.strip()}|{message_content.strip()}|{created_date.strip()}"
        return hashlib.sha256(message_key.encode('utf-8')).hexdigest()

    async def message_exists(self, kode_emiten: str, judul: str, message_content: str, created_date: str) -> bool:
        """
        Check if message already exists in database
        
        Args:
            kode_emiten: Stock code
            judul: Announcement title
            message_content: Full message content
            created_date: Original announcement date

        Returns:
            True if message exists, False otherwise
        """
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False

            message_hash = self._generate_message_hash(kode_emiten, judul, message_content, created_date)

            result = self.client.table('sent_messages').select('id').eq('message_hash', message_hash).execute()
            
            exists = len(result.data) > 0
            if exists:
                logger.info(f"Duplicate message found for {kode_emiten}: {judul}")
            
            return exists
            
        except Exception as e:
            logger.error(f"Error checking message existence: {str(e)}")
            return False
    
    async def save_message(self, kode_emiten: str, judul: str, channel_name: str, 
                          message_content: str, created_date: str = None) -> bool:
        """
        Save sent message to database
        
        Args:
            kode_emiten: Stock code
            judul: Announcement title
            channel_name: Discord channel name
            message_content: Full message content
            created_date: Original announcement date
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return False
            
            message_hash = self._generate_message_hash(kode_emiten, judul, message_content, created_date)
            
            message_data = {
                'message_hash': message_hash,
                'kode_emiten': kode_emiten.strip().upper(),
                'judul': judul.strip(),
                'channel_name': channel_name,
                'message_content': message_content,
                'announcement_date': created_date,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            result = self.client.table('sent_messages').insert(message_data).execute()
            
            if result.data:
                logger.info(f"Message saved to database for {kode_emiten}")
                return True
            else:
                logger.error(f"Failed to save message for {kode_emiten}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving message to database: {str(e)}")
            return False
    
    async def cleanup_old_messages(self, days: int = 30) -> int:
        """
        Clean up old messages from database
        
        Args:
            days: Number of days to keep messages
            
        Returns:
            Number of messages deleted
        """
        try:
            if not self.client:
                logger.error("Supabase client not initialized")
                return 0
            
            cutoff_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            result = self.client.table('sent_messages').delete().lt('sent_at', cutoff_date.isoformat()).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {deleted_count} old messages")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {str(e)}")
            return 0