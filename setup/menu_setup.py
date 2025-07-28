#!/usr/bin/env python3
"""
Jollibee Menu Data Setup for Elasticsearch
Creates menu index with real Jollibee menu data and ELSER semantic search
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, List
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch_client import ElasticsearchClient
from config import Config

logger = logging.getLogger(__name__)

class JollibeeMenuSetup:
    """Setup class for Jollibee menu data with semantic search capabilities"""
    
    def __init__(self):
        """Initialize setup with Elasticsearch client"""
        self.es_client = ElasticsearchClient()
        self.menu_data = []
        logger.info("Initialized Jollibee Menu Setup")
    
    def create_menu_index(self) -> bool:
        """Create menu index with ELSER pipeline mapping"""
        logger.info("Creating menu index with semantic search mapping...")
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "default_pipeline": Config.ELSER_PIPELINE_NAME,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "item_id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "standard"},
                    "category": {"type": "keyword"},
                    "price": {"type": "float"},
                    "description": {"type": "text"},
                    "nutritional_info": {
                        "properties": {
                            "calories": {"type": "integer"},
                            "estimated": {"type": "boolean"}
                        }
                    },
                    "allergens": {"type": "keyword"},
                    "availability": {"type": "boolean"},
                    "is_new": {"type": "boolean"},
                    "is_bestseller": {"type": "boolean"},
                    "points_value": {"type": "integer"},
                    "created_date": {"type": "date"},
                    "searchable_text": {"type": "text"},
                    "ml": {
                        "properties": {
                            "tokens": {"type": "rank_features"}
                        }
                    }
                }
            }
        }
        
        return self.es_client.create_index(Config.INDEX_MENU, mapping)
    
    def generate_menu_data(self) -> List[Dict]:
        """Generate comprehensive menu data from live scraping or fallback"""
        logger.info("Generating menu data...")
        
        if Config.USE_LIVE_MENU_DATA:
            logger.info("🌐 Using live menu scraping")
            try:
                from menu_scraper import JollibeeMenuScraper
                
                scraper = JollibeeMenuScraper()
                scraped_items = scraper.scrape_live_menu()
                
                if scraped_items and len(scraped_items) > 10:
                    logger.info(f"✅ Successfully scraped {len(scraped_items)} live menu items")
                    
                    # Convert scraped items to full menu item format
                    all_menu_items = []
                    for item_data in scraped_items:
                        menu_item = self.create_menu_item(
                            item_data["name"], 
                            item_data["category"], 
                            item_data["price"],
                            is_new=self.is_new_item(item_data["name"]),
                            is_bestseller=self.is_bestseller(item_data["name"])
                        )
                        all_menu_items.append(menu_item)
                    
                    logger.info(f"Generated {len(all_menu_items)} menu items from live data")
                    return all_menu_items
                else:
                    logger.warning("Live scraping returned insufficient data, using fallback")
                    
            except Exception as e:
                logger.error(f"Live menu scraping failed: {str(e)}")
                logger.info("Falling back to static menu data")
        
        # Fallback to hardcoded menu data
        logger.info("📋 Using static menu data")
        return self.get_static_menu_data()
    
    def is_new_item(self, item_name: str) -> bool:
        """Determine if an item is new based on name patterns"""
        new_keywords = ['new', 'limited', 'special', 'ube cheese pie', 'cookies & cream', 'buko pandan']
        return any(keyword in item_name.lower() for keyword in new_keywords)
    
    def is_bestseller(self, item_name: str) -> bool:
        """Determine if an item is a bestseller"""
        bestseller_keywords = ['chickenjoy', 'yumburger', 'jolly spaghetti', 'champ', 'bucket']
        return any(keyword in item_name.lower() for keyword in bestseller_keywords)
    
    def get_static_menu_data(self) -> List[Dict]:
        """Get static fallback menu data"""
        logger.info("Using static fallback menu data...")
        
        # Real Jollibee menu items organized by category
        menu_categories = {
            "Chickenjoy": [
                {"name": "1 Pc Chickenjoy Solo", "price": 82},
                {"name": "1 Pc Chickenjoy with Drink", "price": 116},
                {"name": "2 Pc Chickenjoy Solo", "price": 163},
                {"name": "2 Pc Chickenjoy with Drink", "price": 202},
                {"name": "6 Pc Chickenjoy Bucket Solo", "price": 449},
                {"name": "8 Pc Chickenjoy Bucket Solo", "price": 549},
                {"name": "1 Pc Chickenjoy with Jolly Spaghetti Solo", "price": 132},
                {"name": "1 Pc Chickenjoy with Fries Solo", "price": 128},
                {"name": "1 Pc Chickenjoy with Burger Steak Solo", "price": 132}
            ],
            "Burgers": [
                {"name": "Yumburger Solo", "price": 40},
                {"name": "Yumburger with Drink", "price": 72},
                {"name": "Cheesy Yumburger Solo", "price": 69},
                {"name": "Cheesy Yumburger with Drink", "price": 98},
                {"name": "Double Cheesy Yumburger", "price": 132, "is_new": True},
                {"name": "Champ Solo", "price": 179},
                {"name": "Champ with Fries and Drink", "price": 259},
                {"name": "Amazing Aloha Champ Jr.", "price": 125},
                {"name": "Bacon Cheesy Yumburger Solo", "price": 96}
            ],
            "Jolly Spaghetti": [
                {"name": "Jolly Spaghetti Solo", "price": 60},
                {"name": "Jolly Spaghetti with Drink", "price": 93},
                {"name": "Jolly Spaghetti Family Pan", "price": 237},
                {"name": "Jolly Spaghetti with Burger Steak", "price": 110},
                {"name": "Jolly Spaghetti with Yumburger and Drink", "price": 122}
            ],
            "Family Meals": [
                {"name": "6 Pc Chickenjoy Bucket with Jolly Spaghetti Family Pan", "price": 679},
                {"name": "8 Pc Chickenjoy Bucket with Jolly Spaghetti Family Pan", "price": 774},
                {"name": "4 Pc Chickenjoy Family Box Solo", "price": 326},
                {"name": "6 Pc Chickenjoy with 3 Rice, 3 Jolly Spaghetti & 3 Drinks", "price": 758},
                {"name": "Sweet 6 Pies To-Go", "price": 261}
            ],
            "Breakfast": [
                {"name": "Longganisa Solo", "price": 165},
                {"name": "Beef Tapa Solo", "price": 165},
                {"name": "Corned Beef Solo", "price": 165},
                {"name": "Breakfast Chickenjoy Solo", "price": 148},
                {"name": "2 Pancakes Solo", "price": 82},
                {"name": "Bacon, Egg, & Cheese Sandwich Solo", "price": 95}
            ],
            "Chicken Nuggets": [
                {"name": "6 Pc Chicken Nuggets Solo", "price": 105, "is_new": True},
                {"name": "10 Pc Chicken Nuggets", "price": 186, "is_new": True},
                {"name": "4 PC Chicken Nuggets Kiddie Meal", "price": 120}
            ],
            "Desserts": [
                {"name": "Cookies & Cream Sundae", "price": 59, "is_new": True},
                {"name": "Ube Cheese Pie", "price": 50, "is_new": True},
                {"name": "Buko Pandan Sundae", "price": 63, "is_new": True},
                {"name": "Peach Mango Pie", "price": 48},
                {"name": "Chocolate Sundae Twirl", "price": 50},
                {"name": "Choco Banana Pie", "price": 50}
            ],
            "Beverages": [
                {"name": "Iced Coffee Regular", "price": 64},
                {"name": "Iced Mocha Regular", "price": 64, "is_new": True},
                {"name": "Coke", "price": 53},
                {"name": "Iced Tea", "price": 64},
                {"name": "Hot Chocolate", "price": 51},
                {"name": "Pineapple Juice", "price": 64}
            ],
            "Fries & Sides": [
                {"name": "Regular Fries", "price": 50},
                {"name": "Jolly Crispy Fries – Jumbo", "price": 162},
                {"name": "Creamy Macaroni Soup", "price": 77},
                {"name": "Extra Rice", "price": 32}
            ],
            "Kids Meal": [
                {"name": "Chickenjoy Kids Meal Solo", "price": 142},
                {"name": "Hetty's Twisty Spaghetti Kids Meal Solo", "price": 120},
                {"name": "Yum's Yumburger Solo", "price": 100},
                {"name": "Burger Steak Kids Meal Solo", "price": 120}
            ]
        }
        
        # Mark bestsellers
        bestseller_items = [
            "1 Pc Chickenjoy Solo", "6 Pc Chickenjoy Bucket Solo", "Yumburger Solo",
            "Cheesy Yumburger Solo", "Jolly Spaghetti Solo", "Champ Solo"
        ]
        
        all_menu_items = []
        
        for category, items in menu_categories.items():
            for item_data in items:
                menu_item = self.create_menu_item(
                    item_data["name"], 
                    category, 
                    item_data["price"],
                    is_new=item_data.get("is_new", False),
                    is_bestseller=item_data["name"] in bestseller_items
                )
                all_menu_items.append(menu_item)
        
        logger.info(f"Generated {len(all_menu_items)} menu items across {len(menu_categories)} categories")
        return all_menu_items
    
    def create_menu_item(self, name: str, category: str, price: float, 
                        is_new: bool = False, is_bestseller: bool = False) -> Dict:
        """Create a structured menu item with semantic search text"""
        
        item_id = f"jollibee_{uuid.uuid4().hex[:8]}"
        
        # Generate description based on category and name
        descriptions = {
            "Chickenjoy": "Crispy and juicy fried chicken, Jollibee's signature langhap-sarap dish",
            "Burgers": "Delicious burger with that special langhap-sarap taste",
            "Jolly Spaghetti": "Sweet-style Filipino spaghetti with hotdog and cheese",
            "Family Meals": "Perfect for sharing with family and friends - mas masaya kapag sama-sama",
            "Breakfast": "Filipino breakfast favorites to start your day right",
            "Desserts": "Sweet treats and pies for dessert lovers",
            "Kids Meal": "Kid-friendly meals with special surprises included",
            "Beverages": "Refreshing drinks and coffee options",
            "Fries & Sides": "Crispy sides and accompaniments",
            "Chicken Nuggets": "Bite-sized crispy chicken pieces"
        }
        
        base_description = descriptions.get(category, "Delicious Jollibee menu item")
        
        # Add specific descriptions
        if "bucket" in name.lower():
            description = "Family-sized chicken bucket perfect for sharing - mas masaya kapag marami"
        elif "solo" in name.lower():
            description = f"{base_description} - individual serving"
        elif "with drink" in name.lower():
            description = f"{base_description} served with refreshing drink"
        elif "family" in name.lower():
            description = f"{base_description} - family size portion for sharing"
        else:
            description = base_description
        
        # Calculate nutritional info
        calories = self.estimate_calories(name, category, price)
        allergens = self.get_allergens(name)
        
        # Generate comprehensive searchable text
        searchable_text = self.generate_searchable_text(name, category, description, price, is_new, is_bestseller)
        
        return {
            "item_id": item_id,
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "nutritional_info": {
                "calories": calories,
                "estimated": True
            },
            "allergens": allergens,
            "availability": True,
            "is_new": is_new,
            "is_bestseller": is_bestseller,
            "points_value": max(4, int(price / 10)),
            "created_date": datetime.now().isoformat(),
            "searchable_text": searchable_text
        }
    
    def estimate_calories(self, name: str, category: str, price: float) -> int:
        """Estimate calories based on item type and size"""
        name_lower = name.lower()
        
        if "1 pc chickenjoy" in name_lower:
            return 400
        elif "2 pc chickenjoy" in name_lower:
            return 800
        elif "6 pc chickenjoy" in name_lower:
            return 2400
        elif "8 pc chickenjoy" in name_lower:
            return 3200
        elif "yumburger" in name_lower:
            if "double" in name_lower:
                return 500
            elif "cheesy" in name_lower:
                return 350
            else:
                return 300
        elif "champ" in name_lower:
            return 600
        elif "spaghetti" in name_lower:
            if "family" in name_lower:
                return 1200
            else:
                return 400
        elif "nuggets" in name_lower:
            if "10 pc" in name_lower:
                return 500
            elif "6 pc" in name_lower:
                return 300
            else:
                return 200
        elif "pie" in name_lower or "sundae" in name_lower:
            return 250
        elif "fries" in name_lower:
            if "jumbo" in name_lower:
                return 400
            else:
                return 200
        elif category == "Beverages":
            return 150
        else:
            return max(100, min(800, int(price * 3)))
    
    def get_allergens(self, name: str) -> List[str]:
        """Identify potential allergens in menu items"""
        allergens = []
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['cheese', 'cheesy']):
            allergens.append('dairy')
        if any(keyword in name_lower for keyword in ['egg', 'bacon']):
            allergens.append('eggs')
        if any(keyword in name_lower for keyword in ['spaghetti', 'pie', 'burger']):
            allergens.append('gluten')
        if 'tuna' in name_lower:
            allergens.append('fish')
        
        return allergens
    
    def generate_searchable_text(self, name: str, category: str, description: str, 
                                price: float, is_new: bool, is_bestseller: bool) -> str:
        """Generate comprehensive text for semantic search"""
        
        text_parts = [name, category, description]
        
        # Add price context
        if price <= 50:
            text_parts.append("affordable cheap budget-friendly value student mura")
        elif price <= 150:
            text_parts.append("reasonably priced moderate")
        elif price >= 500:
            text_parts.append("family meal sharing premium group")
        
        # Add special attributes
        if is_new:
            text_parts.append("new latest newest recently introduced bagong")
        if is_bestseller:
            text_parts.append("bestseller popular favorite signature must-try paborito sikat")
        
        # Add category-specific keywords
        category_keywords = {
            "Chickenjoy": "chicken fried crispy juicy signature langhap-sarap manok",
            "Burgers": "burger beef patty sauce bun sandwich",
            "Jolly Spaghetti": "pasta noodles sweet sauce Filipino style hotdog cheese tamis",
            "Family Meals": "sharing family group bucket large portions pamilya",
            "Breakfast": "morning breakfast early meal Filipino traditional almusal",
            "Desserts": "sweet dessert treat pie sundae ice cream matamis",
            "Kids Meal": "children kids family-friendly bata regalo toy",
            "Beverages": "drink beverage coffee cold hot refreshing inumin",
            "Fries & Sides": "side dish fries crispy snack accompaniment",
            "Chicken Nuggets": "bite-size chicken pieces nuggets crispy"
        }
        
        if category in category_keywords:
            text_parts.append(category_keywords[category])
        
        # Add meal size and context
        name_lower = name.lower()
        if "solo" in name_lower:
            text_parts.append("individual single serving one person")
        elif any(keyword in name_lower for keyword in ["family", "bucket", "pan"]):
            text_parts.append("family sharing group multiple people pamilya")
        elif "with drink" in name_lower:
            text_parts.append("combo meal includes beverage complete meal")
        elif "kids" in name_lower:
            text_parts.append("children bata kid-friendly small portion regalo")
        
        # Add Filipino cultural terms
        text_parts.append("jollibee langhap-sarap masarap Filipino pinoy")
        
        return " ".join(text_parts)
    
    def test_semantic_search(self) -> bool:
        """Test semantic search functionality"""
        logger.info("Testing semantic search on menu data...")
        
        test_queries = [
            "family meal crispy chicken sharing",
            "affordable budget student cheap food mura",
            "sweet dessert ice cream matamis",
            "breakfast morning meal almusal",
            "new items latest bagong",
            "bestseller popular paborito"
        ]
        
        success_count = 0
        
        for query in test_queries:
            logger.info(f"Testing query: '{query}'")
            
            results = self.es_client.semantic_search(
                Config.INDEX_MENU,
                query,
                size=3,
                source_fields=["name", "category", "price", "is_new", "is_bestseller"]
            )
            
            if results and results.get('hits', {}).get('hits'):
                hits = results['hits']['hits']
                logger.info(f"  Found {len(hits)} results:")
                
                for i, hit in enumerate(hits, 1):
                    item = hit['_source']
                    badges = []
                    if item.get('is_new'):
                        badges.append('NEW')
                    if item.get('is_bestseller'):
                        badges.append('BESTSELLER')
                    
                    badge_text = f" [{', '.join(badges)}]" if badges else ""
                    logger.info(f"    {i}. {item['name']} - ₱{item['price']} ({item['category']}){badge_text}")
                
                success_count += 1
            else:
                logger.warning(f"  No results found for: {query}")
        
        success_rate = success_count / len(test_queries)
        logger.info(f"Semantic search test results: {success_count}/{len(test_queries)} queries successful ({success_rate:.1%})")
        
        return success_rate >= 0.8  # 80% success rate threshold
    
    def get_menu_statistics(self) -> Dict:
        """Get comprehensive menu statistics"""
        logger.info("Generating menu statistics...")
        
        agg_query = {
            "size": 0,
            "aggs": {
                "categories": {
                    "terms": {"field": "category", "size": 20}
                },
                "price_ranges": {
                    "range": {
                        "field": "price",
                        "ranges": [
                            {"to": 50, "key": "Under ₱50"},
                            {"from": 50, "to": 100, "key": "₱50-100"},
                            {"from": 100, "to": 200, "key": "₱100-200"},
                            {"from": 200, "to": 500, "key": "₱200-500"},
                            {"from": 500, "key": "Over ₱500"}
                        ]
                    }
                },
                "new_items": {
                    "filter": {"term": {"is_new": True}}
                },
                "bestsellers": {
                    "filter": {"term": {"is_bestseller": True}}
                },
                "avg_price": {
                    "avg": {"field": "price"}
                }
            }
        }
        
        results = self.es_client.aggregation_search(Config.INDEX_MENU, agg_query)
        
        if results and results.get('aggregations'):
            aggs = results['aggregations']
            
            stats = {
                "total_items": results['hits']['total']['value'],
                "new_items": aggs['new_items']['doc_count'],
                "bestsellers": aggs['bestsellers']['doc_count'],
                "avg_price": round(aggs['avg_price']['value'], 2),
                "categories": {bucket['key']: bucket['doc_count'] for bucket in aggs['categories']['buckets']},
                "price_ranges": {bucket['key']: bucket['doc_count'] for bucket in aggs['price_ranges']['buckets']}
            }
            
            logger.info(f"Menu Statistics:")
            logger.info(f"  Total Items: {stats['total_items']}")
            logger.info(f"  New Items: {stats['new_items']}")
            logger.info(f"  Bestsellers: {stats['bestsellers']}")
            logger.info(f"  Average Price: ₱{stats['avg_price']}")
            
            return stats
        else:
            logger.error("Failed to generate menu statistics")
            return {}
    
    def run_setup(self) -> bool:
        """Run complete menu setup process"""
        logger.info("🚀 Starting Jollibee Menu Setup with ELSER")
        logger.info("=" * 60)
        
        try:
            # Create menu index
            if not self.create_menu_index():
                logger.error("Failed to create menu index")
                return False
            
            # Generate menu data
            menu_items = self.generate_menu_data()
            if not menu_items:
                logger.error("Failed to generate menu data")
                return False
            
            # Bulk index menu items
            if not self.es_client.bulk_index(Config.INDEX_MENU, menu_items):
                logger.error("Failed to index menu items")
                return False
            
            # Wait for indexing
            import time
            logger.info("⏳ Waiting for ELSER processing...")
            time.sleep(5)
            
            # Refresh index
            self.es_client.refresh_index(Config.INDEX_MENU)
            
            # Test semantic search
            if not self.test_semantic_search():
                logger.warning("Semantic search tests had some failures")
            
            # Generate statistics
            stats = self.get_menu_statistics()
            
            logger.info("✅ Menu setup completed successfully!")
            logger.info("🎉 ELSER-powered semantic search is ready!")
            
            return True
            
        except Exception as e:
            logger.error(f"Menu setup failed: {str(e)}")
            return False

def main():
    """Main setup function"""
    try:
        setup = JollibeeMenuSetup()
        success = setup.run_setup()
        
        if success:
            print("\n🚀 Next Steps:")
            print("1. Run customer data setup")
            print("2. Start the main application")
            print("3. Test semantic search in the web interface")
        else:
            print("\n❌ Menu setup failed. Check logs for details.")
            
        return success
        
    except Exception as e:
        logger.error(f"Setup error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
