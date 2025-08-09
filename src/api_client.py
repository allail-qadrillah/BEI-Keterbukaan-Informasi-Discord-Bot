"""
API client for fetching data from IDX using multiple fetching strategies:
- direct (cloudscraper)
- proxy (cloudscraper with proxy)
- rapidapi (third-party proxy via requests)

Usage:
    client = IDXAPIClient(base_url="https://www.idx.co.id", mode="direct")
    data, status = client.fetch_all_announcements(date_from="20250508")
"""
from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple
from datetime import date, datetime
import cloudscraper
import requests

logger = logging.getLogger(__name__)


class IDXAPIClient:
    """
    Client for interacting with IDX announcement endpoint.

    Modes:
        - "direct": cloudscraper without proxy
        - "proxy": cloudscraper with proxy (pass proxy string or dict)
        - "rapidapi": uses requests to call a third party proxy endpoint;
                      rapidapi_config must be provided (dict with url, headers, and optionally extra query params)
    """

    def __init__(
        self,
        base_url: str,
        mode: str = "direct",
        proxy: Optional[str] = None,
        rapidapi_config: Optional[Dict] = None,
        default_pagesize: int = 2000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.proxy = proxy
        self.rapidapi_config = rapidapi_config or {}
        self.default_pagesize = default_pagesize

        if self.mode in ("direct", "proxy"):
            self.scraper = self._create_scraper()
        else:
            self.scraper = None

    def _create_scraper(self):
        """Create cloudscraper instance and set proxies if requested."""
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        if self.proxy:
            scraper.proxies = {"http": self.proxy, "https": self.proxy}
            logger.info("Cloudscraper created with proxy")
        else:
            logger.info("Cloudscraper created without proxy")
        return scraper

    def _build_default_params(self, date_from: Optional[str], date_to: Optional[str], page_size: int):
        """Return the default params dict for IDX GetAnnouncement endpoint."""
        if date_from is None:
            # default dateFrom far in the past
            date_from = "19000101"
        if date_to is None:
            date_to = datetime.utcnow().strftime("%Y%m%d")

        params = {
            "kodeEmiten": "",
            "emitenType": "*",
            "indexFrom": 0,
            "pageSize": page_size or self.default_pagesize,
            "dateFrom": date_from,
            "dateTo": date_to,
            "lang": "id",
        }
        return params

    def fetch_all_announcements(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page_size: Optional[int] = None,
        timeout: int = 600,
    ) -> Tuple[Optional[Dict], int]:
        """
        Fetch announcements with the configured mode. Returns (json_data, status_code).

        Adjust to the RapidAPI Requests method that you used.
        it used https://rapidapi.com/codeblessed-codeblessed/api/scrapedino

        date_from/date_to should be strings like "20250508" (YYYYMMDD). If None, defaults applied.
        """
        status_code = 0
        try:
            params = self._build_default_params(date_from, date_to, page_size or self.default_pagesize)
            target_path = "/primary/ListedCompany/GetAnnouncement"
            full_url = f"{self.base_url}{target_path}"

            logger.info("Fetching IDX announcements (mode=%s) url=%s params=%s", self.mode, full_url, params)

            if self.mode in ("direct", "proxy"):
                if not self.scraper:
                    self.scraper = self._create_scraper()
                resp = self.scraper.get(full_url, params=params, timeout=timeout)
                status_code = getattr(resp, "status_code", 0)
                if status_code == 200:
                    return resp.json(), status_code
                logger.error("IDX API returned non-200: %s", status_code)
                return None, status_code

            elif self.mode == "rapidapi":
                # rapidapi_config must contain:
                # {
                #   "url": "<rapidapi endpoint>",
                #   "headers": {...},
                #   "extra_query": {...}   # optional
                # }
                rapid_url = self.rapidapi_config.get("url")
                headers = self.rapidapi_config.get("headers", {})
                extra_query = self.rapidapi_config.get("extra_query", {})

                if not rapid_url:
                    raise ValueError("rapidapi_config['url'] must be provided for mode 'rapidapi'")

                # Many CORS proxies expect the real target URL as query param 'url'
                # We'll pass the IDX endpoint as the url param by default, but allow override via extra_query.
                idx_url = full_url + "?" + "&".join(f"{k}={v}" for k, v in params.items())
                query = {"url": idx_url, "method": "GET"}
                query.update(extra_query)
            
                resp = requests.post(rapid_url, headers=headers, json=query, timeout=timeout)
                status_code = getattr(resp, "status_code", 0)
                if status_code == 200:
                    return resp.json(), status_code
                logger.error("RapidAPI proxy returned non-200: %s", status_code)
                return None, status_code

            else:
                raise ValueError(f"Unknown mode: {self.mode}")

        except Exception as exc:  # pragma: no cover - network dependent
            logger.exception("Error fetching announcements: %s", exc)
            return None, status_code or 0
