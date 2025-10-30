import csv
import re
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ASINDataAgent")

EUROLOTS_COST = 3.50  # fixed buy cost per unit (example)
FBA_FEES = 3.55       # base FBA fees (can be improved with Amazon FBA fee table)


class ASINDataAgent:
    def __init__(self, asins_file="asins.csv", output_file="eurolots_test.csv"):
        self.asins_file = asins_file
        self.output_file = output_file

    # ------------------ AMAZON SCRAPER ------------------
    def fetch_amazon_data(self, asin: str, domain="com.be") -> Dict:
        url = f"https://www.amazon.{domain}/dp/{asin}"
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }
        logger.info(f"Fetching Amazon ASIN {asin} from {url}")
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Amazon request failed ({resp.status_code}) for {asin}")
            return {"amazon_asin": asin, "amazon_url": url}

        soup = BeautifulSoup(resp.text, "html.parser")
        data = {"amazon_asin": asin, "amazon_url": url}

        # Title
        title = soup.find(id="productTitle")
        if title:
            data["product_name"] = title.get_text(strip=True)

        # Price
        price_elem = soup.select_one(".a-price .a-offscreen")
        if price_elem:
            price_text = price_elem.get_text().replace("€", "").replace(",", ".").strip()
            try:
                data["amazon_price"] = float(price_text)
            except:
                pass

        # Rating
        rating_elem = soup.select_one("span[data-asin] i span")
        if rating_elem:
            data["amazon_rating"] = rating_elem.get_text().split()[0]

        # Reviews
        reviews_elem = soup.select_one("#acrCustomerReviewText")
        if reviews_elem:
            match = re.search(r"([\d,]+)", reviews_elem.get_text())
            if match:
                data["amazon_reviews"] = match.group(1).replace(",", "")

        # --- Improved Best Sellers Rank extraction ---
        bsr_text = ""
        if (bsr := soup.select_one("#SalesRank")):
            bsr_text = bsr.get_text(" ", strip=True)
        if not bsr_text:
            bullets = soup.select("#detailBulletsWrapper_feature_div li")
            for li in bullets:
                if "Best Sellers Rank" in li.get_text():
                    bsr_text = li.get_text(" ", strip=True)
                    break
        if not bsr_text:
            details = soup.select("#productDetails_detailBullets_sections1 tr")
            for tr in details:
                if "Best Sellers Rank" in tr.get_text():
                    bsr_text = tr.get_text(" ", strip=True)
                    break
        if bsr_text:
            match = re.search(r"#([\d,]+)", bsr_text)
            if match:
                data["amazon_rank"] = match.group(1).replace(",", "")

        return data

    # ------------------ EUROL0TS SCRAPER ------------------
    def search_eurolotus(self, asin: str) -> Dict:
        # Example Eurolots search by ASIN (or use EAN if you have it)
        url = f"https://www.eurolots.com/en/search?s={asin}"
        logger.info(f"Fetching Eurolots for {asin} from {url}")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        product_elem = soup.select_one(".product-miniature")
        if not product_elem:
            return {}

        data = {}
        name_elem = product_elem.select_one(".product-title a")
        if name_elem:
            data["eurolotus_url"] = name_elem["href"]
            data["product_name"] = name_elem.get_text(strip=True)

        # --- Improved price selector ---
        price_elem = product_elem.select_one(".price, .product-price, .price-new")
        if price_elem:
            price_text = price_elem.get_text().replace("€", "").replace(",", ".").strip()
            try:
                data["eurolotus_price"] = float(price_text)
            except:
                pass

        return data

    # ------------------ PROFITABILITY CALCULATOR ------------------
    def calculate_profitability(self, amazon_price: float, eurolots_price: float) -> Dict:
        result = {"net_profit": None, "margin": None, "roi": None, "recommendation": None}

        if not amazon_price or not eurolots_price:
            return result

        total_cost = eurolots_price + EUROLOTS_COST
        fees = FBA_FEES
        net_profit = amazon_price - (total_cost + fees)
        margin = (net_profit / amazon_price) * 100 if amazon_price > 0 else 0
        roi = (net_profit / total_cost) * 100 if total_cost > 0 else 0

        # Recommendation logic
        if net_profit < 0:
            rec = "❌ Low Profit"
        elif roi < 50:
            rec = "⚠️ Slow Sales"
        else:
            rec = "✅ Good Buy"

        result.update({
            "total_cost": round(total_cost, 2),
            "fees": round(fees, 2),
            "net_profit": round(net_profit, 2),
            "margin": round(margin, 1),
            "roi": round(roi, 1),
            "recommendation": rec
        })
        return result

    # ------------------ MAIN RUN ------------------
    def run(self):
        with open(self.asins_file, newline="") as f:
            reader = csv.DictReader(f)
            asins = [row["asin"] for row in reader]

        results: List[Dict] = []
        for asin in asins:
            amazon_data = self.fetch_amazon_data(asin)
            eurolots_data = self.search_eurolotus(asin)

            row = {**amazon_data, **eurolots_data}

            profitability = self.calculate_profitability(
                amazon_price=row.get("amazon_price"),
                eurolots_price=row.get("eurolotus_price", 0)
            )
            row.update(profitability)
            results.append(row)

        # Save to CSV
        fieldnames = [
            "amazon_asin", "amazon_reviews","product_name", "eurolotus_price", "amazon_price", "total_cost", "fees",
            "net_profit", "margin", "roi", "amazon_rank", "recommendation",
            "eurolotus_url", "amazon_url"
        ]
        with open(self.output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Saved results to {self.output_file}")


if __name__ == "__main__":
    agent = ASINDataAgent("asins.csv", "eurolots_test.csv")
    agent.run()
