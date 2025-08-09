"""
Parser for processing API responses and filtering messages
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from config import KeywordConfig

logger = logging.getLogger(__name__)


@dataclass
class AnnouncementMessage:
    """Data class for announcement message"""
    kode_emiten: str
    judul_pengumuman: str
    created_date: str
    attachments: List[Dict]
    original_data: Dict


class MessageParser:
    """Parser for processing IDX API responses"""

    def __init__(self) -> None:
        pass

    def filter_by_keyword(self, announcements: List[Dict], keyword_config: KeywordConfig) -> List[Dict]:
        """
        Filter announcements by keyword configuration

        Args:
            announcements: List of announcement dictionaries (each with 'pengumuman')
            keyword_config: KeywordConfig with include/exclude lists

        Returns:
            Filtered announcements (original dicts)
        """
        filtered: List[Dict] = []

        includes = [inc.lower() for inc in (keyword_config.include or [])]
        excludes = [exc.lower() for exc in (keyword_config.exclude or [])]

        for announcement in announcements:
            judul = announcement.get("pengumuman", {}).get("JudulPengumuman", "") or ""
            judul_low = judul.lower()

            # include must match at least one of include tokens (substring match)
            if not any(inc in judul_low for inc in includes):
                continue

            # exclude must NOT match any exclude tokens
            if any(exc in judul_low for exc in excludes):
                logger.debug("Excluding announcement due to exclude match: %s", judul)
                continue

            filtered.append(announcement)
            logger.debug("Announcement passed filter: %s", judul)

        return filtered

    def parse_announcement(self, announcement_data: Dict) -> Optional[AnnouncementMessage]:
        """Parse one announcement dict into AnnouncementMessage"""
        try:
            pengumuman = announcement_data.get("pengumuman", {})
            attachments = announcement_data.get("attachments", [])

            kode = pengumuman.get("Kode_Emiten", "") or ""
            judul = pengumuman.get("JudulPengumuman", "") or ""
            created = pengumuman.get("CreatedDate", "") or pengumuman.get("TglPengumuman", "")

            return AnnouncementMessage(
                kode_emiten=kode.strip(),
                judul_pengumuman=judul.strip(),
                created_date=self._format_date(created),
                attachments=attachments,
                original_data=announcement_data,
            )
        except Exception as e:
            logger.exception("Error parsing announcement: %s", e)
            return None

    def _format_date(self, date_str: str) -> str:
        """Format date-like strings into readable ISO datetime string"""
        if not date_str:
            return ""
        try:
            # Some dates are already ISO, some not. Try parsing robustly.
            # e.g. "2025-08-08T23:30:21" -> parse directly
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # fallback: return original
            return date_str

    def format_message(self, announcement: AnnouncementMessage) -> str:
        """Create a formatted message string suitable for Discord"""
        message = f"**{announcement.kode_emiten}** | {announcement.created_date}\n\n{announcement.judul_pengumuman}\n"

        if announcement.attachments:
            message += "\n**Files:**\n"
            for attachment in announcement.attachments:
                filename = attachment.get("OriginalFilename") or attachment.get("PDFFilename") or "Unknown"
                file_url = attachment.get("FullSavePath", "") or ""
                if file_url:
                    message += f"• [{filename}]({file_url})\n"
                else:
                    message += f"• {filename}\n"
            message += "\n"

        message += "====================================\n"
        return message
