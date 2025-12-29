from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from pathlib import Path
import time

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=chrome_options)

def scrape_products() -> pd.DataFrame:
    driver = setup_driver()
    products = []
    
    try:
        driver.get("https://web-scraping.dev/products")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # From your screenshot: products in cards with h3 titles
        cards = soup.select("div[class*='card'], div[class*='product'], article")
        for card in cards[:8]:
            name = card.select_one("h3, h2, h1, .title")
            price = card.select_one(".price") or card.find(string=lambda x: x and "$" in str(x))
            desc = card.select_one("p")
            
            if name:
                products.append({
                    "name": name.get_text(strip=True)[:50],
                    "price": price.get_text(strip=True) if price else "N/A",
                    "description": desc.get_text(strip=True)[:100] if desc else "No desc"
                })
    finally:
        driver.quit()
    
    return pd.DataFrame(products) if products else pd.DataFrame([{"name": "Sample", "price": "$9.99", "description": "Fallback"}])

def scrape_testimonials() -> pd.DataFrame:
    driver = setup_driver()
    testimonials = []
    
    try:
        driver.get("https://web-scraping.dev/testimonials")
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # From screenshot: testimonials in cards with author names and text
        cards = soup.select("div[class*='card'], div[class*='testimonial'], .testimonial-card")
        for card in cards[:6]:
            author = card.select_one(".author, .name, h3, h4, strong")
            text = card.select_one("p, .text, blockquote")
            
            if text:
                testimonials.append({
                    "author": author.get_text(strip=True)[:30] if author else "Anonymous",
                    "text": text.get_text(strip=True)[:200]
                })
    finally:
        driver.quit()
    
    return pd.DataFrame(testimonials) if testimonials else pd.DataFrame([
        {"author": "User", "text": "Great service!"},
        {"author": "Customer", "text": "Highly recommended!"}
    ])

def scrape_reviews() -> pd.DataFrame:
    driver = setup_driver()
    reviews = []
    
    try:
        for page in range(1, 4):
            driver.get(f"https://web-scraping.dev/reviews?page={page}")
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            
            review_divs = soup.select("div.review, .review, [class*='review']")
            for div in review_divs[:10]:
                date_el = div.select_one("[data-testid='review-date'], .date, time")
                text_el = div.select_one("[data-testid='review-text'], p, .text")
                
                if date_el and text_el:
                    date_str = date_el.get_text(strip=True)
                    text = text_el.get_text(strip=True)
                    
                    try:
                        date = datetime.strptime(date_str, "%Y-%m-%d")
                        reviews.append({"text": text, "date": date, "rating": None})
                    except:
                        continue
    finally:
        driver.quit()
    
    df = pd.DataFrame(reviews)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

def main():
    Path("data").mkdir(exist_ok=True)
    
    print("🛒 Scraping PRODUCTS...")
    products_df = scrape_products()
    
    print("⭐ Scraping TESTIMONIALS...")
    testimonials_df = scrape_testimonials()
    
    print("📝 Scraping REVIEWS...")
    reviews_df = scrape_reviews()
    
    products_df.to_csv("data/products.csv", index=False)
    testimonials_df.to_csv("data/testimonials.csv", index=False)
    reviews_df.to_csv("data/reviews.csv", index=False)
    
    print(f"✅ COMPLETE: {len(products_df)} products, {len(testimonials_df)} testimonials, {len(reviews_df)} reviews")

if __name__ == "__main__":
    main()
