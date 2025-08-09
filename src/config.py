"""
Configuration settings for IDX Discord Bot
"""

from __future__ import annotations

import os
from typing import Dict, List
from dataclasses import dataclass
from dotenv import load_dotenv
import json

load_dotenv()


@dataclass
class KeywordConfig:
    include: List[str]
    exclude: List[str] = None

    def __post_init__(self):
        if self.exclude is None:
            self.exclude = []


class Config:
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    GUILD_ID = os.getenv("DISCORD_GUILD_ID")
    if not DISCORD_TOKEN or not GUILD_ID:
        raise ValueError(
            "DISCORD_TOKEN and DISCORD_GUILD_ID must be set in environment variables"
        )

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables"
        )

    IDX_API_URL = os.getenv("IDX_API_URL", "https://www.idx.co.id")

    # Fetch mode: direct / proxy / rapidapi
    IDX_FETCH_MODE = os.getenv("IDX_FETCH_MODE", "direct")
    PROXY = os.getenv(
        "PROXY"
    )  # for cloudscraper proxy string e.g. "http://username:pass@host:port"

    # Example RAPIDAPI_CONFIG env: JSON string with keys url, headers (dict), extra_query (dict)
    # e.g. RAPIDAPI_CONFIG='{"url":"https://cors-proxy4.p.rapidapi.com/","headers":{"x-rapidapi-key":"xxx","x-rapidapi-host":"cors-proxy4.p.rapidapi.com"}}'
    rapidapi_raw = os.getenv("RAPIDAPI_CONFIG")
    if rapidapi_raw:
        try:
            RAPIDAPI_CONFIG = json.loads(rapidapi_raw)
        except Exception:
            RAPIDAPI_CONFIG = {}
    else:
        RAPIDAPI_CONFIG = {}

    # Keyword configurations - Easy to modify
    KEYWORDS: Dict[str, KeywordConfig] = {
        "Pengambilalihan": KeywordConfig(include=["Pengambilalihan"]),
        "Penjelasan atas Pemberitaan Media Massa": KeywordConfig(
            include=["Penjelasan atas Pemberitaan Media Massa"]
        ),
        "Negosiasi": KeywordConfig(include=["Negosiasi"], exclude=["Pasar Negosiasi"]),
    }

    CHANNEL_MAPPING = {
        "Pengambilalihan": "pengambilalihan-alerts",
        "Penjelasan atas Pemberitaan Media Massa": "pemberitaan-media-massa-alerts",
        "Negosiasi": "negosiasi-alerts",
        "Error": "error-logs",
    }
