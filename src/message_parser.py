"""
Parser for processing API responses and filtering messages
"""
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
    
    def __init__(self):
        """Initialize message parser"""
        pass
    
    def filter_by_keyword(self, announcements: List[Dict], keyword_config: KeywordConfig) -> List[Dict]:
        """
        Filter announcements by keyword configuration
        
        Args:
            announcements: List of announcement data
            keyword_config: Keyword configuration with include/exclude rules
            
        Returns:
            Filtered list of announcements
        """
        filtered = []
        
        for announcement in announcements:
            judul = announcement.get('pengumuman', {}).get('JudulPengumuman', '').lower()
            
            # Check if any include keyword is present
            include_match = any(include.lower() in judul for include in keyword_config.include)
            
            if not include_match:
                continue
            
            # Check if any exclude keyword is present
            exclude_match = any(exclude.lower() in judul for exclude in keyword_config.exclude)
            
            if not exclude_match:
                filtered.append(announcement)
                logger.debug(f"Announcement passed filter: {judul}")
            else:
                logger.debug(f"Announcement excluded: {judul}")
        
        return filtered
    
    def parse_announcement(self, announcement_data: Dict) -> Optional[AnnouncementMessage]:
        """
        Parse announcement data into structured message
        
        Args:
            announcement_data: Raw announcement data from API
            
        Returns:
            Parsed announcement message or None if invalid
        """
        try:
            pengumuman = announcement_data.get('pengumuman', {})
            attachments = announcement_data.get('attachments', [])
            
            return AnnouncementMessage(
                kode_emiten=pengumuman.get('Kode_Emiten', '').strip(),
                judul_pengumuman=pengumuman.get('JudulPengumuman', ''),
                created_date=self._format_date(pengumuman.get('CreatedDate', '')),
                attachments=attachments,
                original_data=announcement_data
            )
        except Exception as e:
            logger.error(f"Error parsing announcement: {str(e)}")
            return None
    
    def _format_date(self, date_str: str) -> str:
        """
        Format date string to readable format
        
        Args:
            date_str: ISO date string
            
        Returns:
            Formatted date string
        """
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return date_str
    
    def format_message(self, announcement: AnnouncementMessage) -> str:
        """
        Format announcement into Discord message with better spacing
        
        Args:
            announcement: Parsed announcement data
            
        Returns:
            Formatted message string
        """
        message = f"**{announcement.kode_emiten}** | {announcement.created_date}\n\n{announcement.judul_pengumuman}\n"
        
        if announcement.attachments:
            message += "\n**Files:**\n"
            for attachment in announcement.attachments:
                filename = attachment.get('OriginalFilename', 'Unknown')
                file_url = attachment.get('FullSavePath', '')
                if file_url:
                    message += f"• [{filename}]({file_url})\n"
                else:
                    message += f"• {filename}\n"
            
            # Add extra spacing after files section
            message += "\n"
        
        # Add extra spacing at the end for better readability
        message += "====================================\n"
        
        return message