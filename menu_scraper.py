#!/usr/bin/env python3
"""
Jollibee Live Menu Scraper
Fetches real menu data from jollibeemenuprice.ph
"""

import requests
import re
import time
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class JollibeeMenuScraper:
    """Scraper for live Jollibee menu data"""
    
    def __init__(self):
        """Initialize the menu scraper"""
        self.base_url = Config.JOLLIBEE_MENU_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        logger.info(f"Initialized menu scraper for: {self.base_url}")
    
    def fetch_menu_page(self) -> Optional[BeautifulSoup]:
        """Fetch the main menu page"""
        try:
            logger.info(f"Fetching menu from: {self.base_url}")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            logger.info("Successfully fetched menu page")
            return soup
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch menu page: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing menu page: {str(e)}")
            return None
    
    def extract_price(self, price_text: str) -> float:
        """Extract price from text"""
        if not price_text:
            return 0.0
        
        # Remove currency symbols and clean up
        price_clean = re.sub(r'[^\d.,]', '', price_text)
        price_clean = price_clean.replace(',', '')
        
        try:
            return float(price_clean)
        except ValueError:
            logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    def categorize_item(self, item_name: str) -> str:
        """Categorize menu item based on name"""
        name_lower = item_name.lower()
        
        # Category mapping based on item names
        if any(keyword in name_lower for keyword in ['chickenjoy', 'chicken']):
            if 'bucket' in name_lower or 'family' in name_lower:
                return "Family Meals"
            else:
                return "Chickenjoy"
        elif any(keyword in name_lower for keyword in ['burger', 'yum', 'champ']):
            return "Burgers"
        elif 'spaghetti' in name_lower:
            return "Jolly Spaghetti"
        elif any(keyword in name_lower for keyword in ['nugget', 'nuggets']):
            return "Chicken Nuggets"
        elif any(keyword in name_lower for keyword in ['breakfast', 'longganisa', 'tapa', 'corned', 'pancake']):
            return "Breakfast"
        elif any(keyword in name_lower for keyword in ['pie', 'sundae', 'dessert', 'ice cream', 'chocolate']):
            return "Desserts"
        elif any(keyword in name_lower for keyword in ['coffee', 'drink', 'coke', 'sprite', 'juice', 'tea']):
            return "Beverages"
        elif any(keyword in name_lower for keyword in ['fries', 'rice', 'soup']):
            return "Fries & Sides"
        elif any(keyword in name_lower for keyword in ['kids', 'kiddie']):
            return "Kids Meal"
        elif any(keyword in name_lower for keyword in ['family', 'bucket', '6 pc', '8 pc']):
            return "Family Meals"
        else:
            return "Main Dishes"
    
    def parse_menu_items(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse menu items from the webpage"""
        menu_items = []
        
        try:
            # Look for different possible selectors for menu items
            selectors_to_try = [
                '.menu-item',
                '.product-item', 
                '.food-item',
                '.item',
                '[class*="menu"]',
                '[class*="product"]',
                'tr',  # Table rows
                'li'   # List items
            ]
            
            items_found = []
            
            for selector in selectors_to_try:
                elements = soup.select(selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    for element in elements:
                        item_data = self.extract_item_from_element(element)
                        if item_data and item_data['name'] and item_data['price'] > 0:
                            items_found.append(item_data)
                    
                    if items_found:
                        break
            
            # If structured parsing fails, try text pattern matching
            if not items_found:
                logger.info("Structured parsing failed, trying text pattern matching...")
                items_found = self.parse_menu_from_text(soup.get_text())
            
            # Remove duplicates and clean up
            seen_names = set()
            for item in items_found:
                if item['name'] not in seen_names:
                    menu_items.append(item)
                    seen_names.add(item['name'])
            
            logger.info(f"Successfully parsed {len(menu_items)} unique menu items")
            return menu_items
            
        except Exception as e:
            logger.error(f"Error parsing menu items: {str(e)}")
            return []
    
    def extract_item_from_element(self, element) -> Optional[Dict]:
        """Extract item data from a single element"""
        try:
            # Get text content
            text = element.get_text(strip=True)
            
            # Look for name and price patterns
            # Common patterns: "Item Name - ₱99" or "Item Name ₱99"
            price_patterns = [
                r'(.+?)\s*[-–—]\s*₱?\s*(\d+(?:\.\d{2})?)',
                r'(.+?)\s*₱\s*(\d+(?:\.\d{2})?)',
                r'(.+?)\s*PHP?\s*(\d+(?:\.\d{2})?)',
                r'(.+?)\s*(\d+(?:\.\d{2})?)\s*(?:pesos?|php|₱)',
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    price = float(match.group(2))
                    
                    if len(name) > 3 and price > 0:  # Basic validation
                        return {
                            'name': name,
                            'price': price,
                            'category': self.categorize_item(name)
                        }
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract item from element: {str(e)}")
            return None
    
    def parse_menu_from_text(self, text: str) -> List[Dict]:
        """Parse menu items from raw text using patterns"""
        items = []
        
        # Split text into lines and look for menu item patterns
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for patterns like "Item Name ₱99" or "Item Name - ₱99"
            patterns = [
                r'(.+?)\s*[-–—]\s*₱\s*(\d+(?:\.\d{2})?)',
                r'(.+?)\s*₱\s*(\d+(?:\.\d{2})?)',
                r'(.+?)\s*(\d+(?:\.\d{2})?)\s*pesos?',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    try:
                        price = float(match.group(2))
                        
                        # Basic validation
                        if (len(name) > 3 and 
                            price > 0 and 
                            price < 2000 and  # Reasonable price range
                            not any(skip in name.lower() for skip in ['menu', 'category', 'section', 'price', 'total'])):
                            
                            items.append({
                                'name': name,
                                'price': price,
                                'category': self.categorize_item(name)
                            })
                            break
                    except ValueError:
                        continue
        
        logger.info(f"Extracted {len(items)} items from text parsing")
        return items
    
    def get_fallback_menu(self) -> List[Dict]:
        """Return fallback menu data if scraping fails"""
        logger.info("Using fallback menu data")
        
        fallback_items = [
            {"name": "1 Pc Chickenjoy Solo", "price": 82, "category": "Chickenjoy"},
            {"name": "2 Pc Chickenjoy Solo", "price": 163, "category": "Chickenjoy"},
            {"name": "6 Pc Chickenjoy Bucket Solo", "price": 449, "category": "Family Meals"},
            {"name": "8 Pc Chickenjoy Bucket Solo", "price": 549, "category": "Family Meals"},
            {"name": "Yumburger Solo", "price": 40, "category": "Burgers"},
            {"name": "Cheesy Yumburger Solo", "price": 69, "category": "Burgers"},
            {"name": "Champ Solo", "price": 179, "category": "Burgers"},
            {"name": "Jolly Spaghetti Solo", "price": 60, "category": "Jolly Spaghetti"},
            {"name": "Jolly Spaghetti Family Pan", "price": 237, "category": "Jolly Spaghetti"},
            {"name": "Regular Fries", "price": 50, "category": "Fries & Sides"},
            {"name": "Peach Mango Pie", "price": 48, "category": "Desserts"},
            {"name": "Iced Coffee Regular", "price": 64, "category": "Beverages"},
            {"name": "Coke", "price": 53, "category": "Beverages"},
            {"name": "Chickenjoy Kids Meal Solo", "price": 142, "category": "Kids Meal"},
        ]
        
        return fallback_items
    
    def scrape_live_menu(self) -> List[Dict]:
        """Main method to scrape live menu data"""
        logger.info("🌐 Starting live menu scraping...")
        
        if not Config.USE_LIVE_MENU_DATA:
            logger.info("Live menu scraping disabled, using fallback data")
            return self.get_fallback_menu()
        
        try:
            # Fetch the webpage
            soup = self.fetch_menu_page()
            if not soup:
                logger.warning("Could not fetch menu page, using fallback")
                return self.get_fallback_menu()
            
            # Parse menu items
            menu_items = self.parse_menu_items(soup)
            
            if not menu_items:
                logger.warning("No menu items found, using fallback")
                return self.get_fallback_menu()
            
            if len(menu_items) < 5:  # Too few items, probably parsing failed
                logger.warning(f"Only {len(menu_items)} items found, using fallback")
                return self.get_fallback_menu()
            
            logger.info(f"✅ Successfully scraped {len(menu_items)} live menu items")
            
            # Add metadata
            for item in menu_items:
                item['scraped_at'] = datetime.now().isoformat()
                item['source'] = 'live_scraping'
            
            return menu_items
            
        except Exception as e:
            logger.error(f"Live menu scraping failed: {str(e)}")
            logger.info("Falling back to static menu data")
            return self.get_fallback_menu()
    
    def display_scraped_menu(self, menu_items: List[Dict]):
        """Display scraped menu for debugging"""
        print(f"\n📋 Scraped Menu Items ({len(menu_items)} total):")
        print("=" * 60)
        
        # Group by category
        categories = {}
        for item in menu_items:
            category = item['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        
        for category, items in categories.items():
            print(f"\n🍽️ {category} ({len(items)} items):")
            for item in sorted(items, key=lambda x: x['price']):
                print(f"   • {item['name']} - ₱{item['price']}")

def main():
    """Test the menu scraper"""
    scraper = JollibeeMenuScraper()
    menu_items = scraper.scrape_live_menu()
    scraper.display_scraped_menu(menu_items)
    
    if menu_items:
        print(f"\n✅ Successfully scraped {len(menu_items)} items")
        print(f"📊 Categories found: {len(set(item['category'] for item in menu_items))}")
        print(f"💰 Price range: ₱{min(item['price'] for item in menu_items)} - ₱{max(item['price'] for item in menu_items)}")
    else:
        print("❌ No menu items scraped")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
