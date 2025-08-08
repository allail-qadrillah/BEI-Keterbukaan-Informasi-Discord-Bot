import cloudscraper
import json
from datetime import datetime
# Inisialisasi scraper
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

# URL dan parameter
url = "https://www.idx.co.id/primary/ListedCompany/GetAnnouncement"
params = {
            "kodeEmiten": "",
            "emitenType": "*",
            "indexFrom": 0,
            "pageSize": 2,
            "dateFrom": "19010101",
            "dateTo": datetime.now().strftime("%Y%m%d"),
            "lang": "id",
            "keyword": "pengambilalihan"
}

# Lakukan GET request
response = scraper.get(url, params=params)

# Cek hasil
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print(f"Request gagal. Status code: {response.status_code}")
