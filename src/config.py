"""
Configuration settings for IDX Discord Bot
"""
import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class KeywordConfig:
    """Configuration for keyword filtering"""
    include: List[str]
    exclude: List[str] = None
    
    def __post_init__(self):
        if self.exclude is None:
            self.exclude = []

class Config:
    """Main configuration class for the bot"""
    
    # Discord settings
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    GUILD_ID = os.getenv('DISCORD_GUILD_ID')
    if not DISCORD_TOKEN or not GUILD_ID:
        raise ValueError("DISCORD_TOKEN and GUILD_ID must be set in environment variables")

    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_KEY')
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables")
    
    # API settings
    IDX_API_URL = "https://www.idx.co.id"
    
    # Keyword configurations - Easy to modify
    KEYWORDS = {
        "Pengambilalihan": KeywordConfig(
            include=["Pengambilalihan"]
        ),
        "Penjelasan atas Pemberitaan Media Massa": KeywordConfig(
            include=["Penjelasan atas Pemberitaan Media Massa"]
        ),
        "Negosiasi": KeywordConfig(
            include=["Negosiasi"],
            exclude=["Pasar Negosiasi"]
        )
    }
    
    # Discord channel mapping
    CHANNEL_MAPPING = {
        "Pengambilalihan": "pengambilalihan-alerts",
        "Penjelasan atas Pemberitaan Media Massa": "pemberitaan-media-massa-alerts",
        "Negosiasi": "negosiasi-alerts",
        
        "Error": "error-logs"
    }

    # Proxy settings
    PROXY = os.getenv('PROXY')