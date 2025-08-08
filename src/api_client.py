"""
API client for fetching data from IDX using cloudscraper
"""
import cloudscraper
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class IDXAPIClient:
    """Client for interacting with IDX API using CloudScraper"""

    def __init__(self, base_url: str):
        """
        Initialize API client

        Args:
            base_url: Base URL for IDX API
            default_params: Default parameters for API requests
        """
        self.base_url = base_url
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )

    def fetch_announcements(self, keyword: str) -> Optional[Dict]:
        """
        Fetch announcements from IDX API

        Args:
            keyword: Search keyword

        Returns:
            API response data or None if failed
        """
        params = {
            "kodeEmiten": "",
            "emitenType": "*",
            "indexFrom": 0,
            "pageSize": 5, # Adjust page size as needed
            "dateFrom": "19010101",
            "dateTo": datetime.now().strftime("%Y%m%d"),
            "lang": "id",
            "keyword": keyword
        }

        try:
            response = self.scraper.get(self.base_url + "/primary/ListedCompany/GetAnnouncement", params=params)
            status_code = response.status_code
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched {len(data.get('Replies', []))} announcements for keyword: {keyword}")
                return data, status_code
            else:
                logger.error(f"API request failed with status {response.status_code}")
                return None, status_code
        except Exception as e:
            logger.error(f"Error fetching announcements: {str(e)}")
            return None, status_code
