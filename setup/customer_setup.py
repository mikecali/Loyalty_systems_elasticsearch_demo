#!/usr/bin/env python3
"""
Jollibee Customer Data Setup for Elasticsearch
Creates customer and related indices with sample data
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch_client import ElasticsearchClient
from config import Config

logger = logging.getLogger(__name__)

class JollibeeCustomerSetup:
    """Setup class for customer data and related indices"""
    
    def __init__(self):
        """Initialize setup with Elasticsearch client"""
        self.es_client = ElasticsearchClient()
        logger.info("Initialized Jollibee Customer Setup")
    
    def create_customer_index(self) -> bool:
        """Create customer index with proper mapping"""
        logger.info("Creating customer index...")
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "default_pipeline": Config.ELSER_PIPELINE_NAME,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "customer_id": {"type": "keyword"},
                    "personal_info": {
                        "properties": {
                            "name": {"type": "text"},
                            "email": {"type": "keyword"},
                            "phone": {"type": "keyword"},
                            "age": {"type": "integer"},
                            "gender": {"type": "keyword"},
                            "address": {"type": "text"}
                        }
                    },
                    "loyalty_profile": {
                        "properties": {
                            "tier": {"type": "keyword"},
                            "total_points": {"type": "integer"},
                            "points_earned_ytd": {"type": "integer"},
                            "points_redeemed_ytd": {"type": "integer"},
                            "annual_spending": {"type": "float"},
                            "membership_since": {"type": "date"},
                            "last_activity": {"type": "date"}
                        }
                    },
                    "preferences": {
                        "properties": {
                            "favorite_items": {"type": "keyword"},
                            "dietary_restrictions": {"type": "keyword"},
                            "preferred_channels": {"type": "keyword"}
                        }
                    },
                    "purchase_behavior": {
                        "properties": {
                            "total_orders": {"type": "integer"},
                            "avg_order_value": {"type": "float"},
                            "frequency_score": {"type": "float"},
                            "last_order_date": {"type": "date"}
                        }
                    },
                    "searchable_text": {"type": "text"},
                    "ml": {
                        "properties": {
                            "tokens": {"type": "rank_features"}
                        }
                    }
                }
            }
        }
        
        return self.es_client.create_index(Config.INDEX_CUSTOMERS, mapping)
    
    def create_transactions_index(self) -> bool:
        """Create transactions index"""
        logger.info("Creating transactions index...")
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "transaction_id": {"type": "keyword"},
                    "customer_id": {"type": "keyword"},
                    "store_id": {"type": "keyword"},
                    "timestamp": {"type": "date"},
                    "channel": {"type": "keyword"},
                    "location": {
                        "properties": {
                            "store_id": {"type": "keyword"},
                            "store_name": {"type": "text"},
                            "coordinates": {
                                "properties": {
                                    "lat": {"type": "float"},
                                    "lon": {"type": "float"}
                                }
                            }
                        }
                    },
                    "items": {
                        "type": "nested",
                        "properties": {
                            "name": {"type": "text"},
                            "price": {"type": "float"},
                            "quantity": {"type": "integer"}
                        }
                    },
                    "order_total": {"type": "float"},
                    "points_earned": {"type": "integer"},
                    "points_redeemed": {"type": "integer"},
                    "payment_method": {"type": "keyword"},
                    "order_type": {"type": "keyword"},
                    "hour_of_day": {"type": "integer"},
                    "day_of_week": {"type": "keyword"},
                    "is_weekend": {"type": "boolean"},
                    "bulk_simulation": {"type": "boolean"},
                    "scenario": {"type": "keyword"}
                }
            }
        }
        
        return self.es_client.create_index(Config.INDEX_TRANSACTIONS, mapping)
    
    def create_stores_index(self) -> bool:
        """Create stores index"""
        logger.info("Creating stores index...")
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "store_id": {"type": "keyword"},
                    "store_name": {"type": "text"},
                    "location": {"type": "text"},
                    "address": {"type": "text"},
                    "store_type": {"type": "keyword"},
                    "operating_hours": {
                        "properties": {
                            "open": {"type": "keyword"},
                            "close": {"type": "keyword"},
                            "is_24h": {"type": "boolean"}
                        }
                    },
                    "coordinates": {
                        "properties": {
                            "lat": {"type": "float"},
                            "lon": {"type": "float"}
                        }
                    },
                    "features": {"type": "keyword"},
                    "status": {"type": "keyword"}
                }
            }
        }
        
        return self.es_client.create_index(Config.INDEX_STORES, mapping)
    
    def create_inventory_index(self) -> bool:
        """Create inventory index"""
        logger.info("Creating inventory index...")
        
        mapping = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "refresh_interval": "1s"
            },
            "mappings": {
                "properties": {
                    "inventory_id": {"type": "keyword"},
                    "store_id": {"type": "keyword"},
                    "item_name": {"type": "text"},
                    "item_category": {"type": "keyword"},
                    "current_stock": {"type": "integer"},
                    "reorder_point": {"type": "integer"},
                    "max_stock": {"type": "integer"},
                    "daily_consumption": {"type": "float"},
                    "status": {"type": "keyword"},
                    "last_restocked": {"type": "date"},
                    "predicted_stockout_date": {"type": "date"},
                    "supplier": {"type": "keyword"},
                    "unit_cost": {"type": "float"},
                    "timestamp": {"type": "date"}
                }
            }
        }
        
        return self.es_client.create_index(Config.INDEX_INVENTORY, mapping)
    
    def create_sample_customers(self) -> List[Dict]:
        """Create sample customer data"""
        logger.info("Generating sample customer data...")
        
        customers = [
            {
                "customer_id": "mike001",
                "personal_info": {
                    "name": "Mike Santos",
                    "email": "mike.santos@email.com",
                    "phone": "+639171234567",
                    "age": 35,
                    "gender": "M",
                    "address": "Quezon City, Metro Manila"
                },
                "loyalty_profile": {
                    "tier": "BeeElite",
                    "total_points": 2856,
                    "points_earned_ytd": 4200,
                    "points_redeemed_ytd": 1344,
                    "annual_spending": 7500.00,
                    "membership_since": "2020-03-15T00:00:00",
                    "last_activity": datetime.now().isoformat()
                },
                "preferences": {
                    "favorite_items": ["Chickenjoy", "Family Bucket", "Jolly Spaghetti"],
                    "dietary_restrictions": [],
                    "preferred_channels": ["dine-in", "app"]
                },
                "purchase_behavior": {
                    "total_orders": 68,
                    "avg_order_value": 425.50,
                    "frequency_score": 8.5,
                    "last_order_date": (datetime.now() - timedelta(days=3)).isoformat()
                },
                "searchable_text": "Mike Santos family customer BeeElite tier chickenjoy bucket family meals high spending frequent visitor dine-in app orders pamilya"
            },
            {
                "customer_id": "zander001",
                "personal_info": {
                    "name": "Zander Cruz",
                    "email": "zander.cruz@email.com",
                    "phone": "+639181234567",
                    "age": 28,
                    "gender": "M",
                    "address": "Makati City, Metro Manila"
                },
                "loyalty_profile": {
                    "tier": "BeeFan",
                    "total_points": 1245,
                    "points_earned_ytd": 2100,
                    "points_redeemed_ytd": 855,
                    "annual_spending": 3200.00,
                    "membership_since": "2021-06-20T00:00:00",
                    "last_activity": datetime.now().isoformat()
                },
                "preferences": {
                    "favorite_items": ["Champ", "Chicken Sandwich", "Iced Coffee"],
                    "dietary_restrictions": [],
                    "preferred_channels": ["app", "delivery"]
                },
                "purchase_behavior": {
                    "total_orders": 42,
                    "avg_order_value": 185.20,
                    "frequency_score": 6.8,
                    "last_order_date": (datetime.now() - timedelta(days=1)).isoformat()
                },
                "searchable_text": "Zander Cruz young professional BeeFan tier mobile app delivery quick meals burgers coffee convenience working adult"
            },
            {
                "customer_id": "john001",
                "personal_info": {
                    "name": "John Dela Cruz",
                    "email": "john.delacruz@email.com",
                    "phone": "+639191234567",
                    "age": 42,
                    "gender": "M",
                    "address": "Pasig City, Metro Manila"
                },
                "loyalty_profile": {
                    "tier": "BeeFan",
                    "total_points": 890,
                    "points_earned_ytd": 1580,
                    "points_redeemed_ytd": 690,
                    "annual_spending": 2800.00,
                    "membership_since": "2019-11-10T00:00:00",
                    "last_activity": datetime.now().isoformat()
                },
                "preferences": {
                    "favorite_items": ["Chickenjoy", "Burger Steak", "Peach Mango Pie"],
                    "dietary_restrictions": [],
                    "preferred_channels": ["dine-in"]
                },
                "purchase_behavior": {
                    "total_orders": 25,
                    "avg_order_value": 220.80,
                    "frequency_score": 4.2,
                    "last_order_date": (datetime.now() - timedelta(days=7)).isoformat()
                },
                "searchable_text": "John Dela Cruz weekend customer BeeFan tier traditional items chickenjoy burger steak desserts occasional diner family man"
            },
            {
                "customer_id": "melvin001",
                "personal_info": {
                    "name": "Melvin Reyes",
                    "email": "melvin.reyes@email.com",
                    "phone": "+639201234567",
                    "age": 20,
                    "gender": "M",
                    "address": "University Belt, Manila"
                },
                "loyalty_profile": {
                    "tier": "BeeBuddy",
                    "total_points": 324,
                    "points_earned_ytd": 680,
                    "points_redeemed_ytd": 356,
                    "annual_spending": 980.00,
                    "membership_since": "2022-08-01T00:00:00",
                    "last_activity": datetime.now().isoformat()
                },
                "preferences": {
                    "favorite_items": ["Yumburger", "Regular Fries", "Coke"],
                    "dietary_restrictions": [],
                    "preferred_channels": ["dine-in", "app"]
                },
                "purchase_behavior": {
                    "total_orders": 28,
                    "avg_order_value": 65.50,
                    "frequency_score": 5.1,
                    "last_order_date": (datetime.now() - timedelta(days=2)).isoformat()
                },
                "searchable_text": "Melvin Reyes student customer BeeBuddy tier budget conscious yumburger value meals affordable options estudyante mura"
            },
            {
                "customer_id": "carms001",
                "personal_info": {
                    "name": "Carmela Garcia",
                    "email": "carmela.garcia@email.com",
                    "phone": "+639211234567",
                    "age": 38,
                    "gender": "F",
                    "address": "Alabang, Muntinlupa"
                },
                "loyalty_profile": {
                    "tier": "BeeFan",
                    "total_points": 1567,
                    "points_earned_ytd": 2890,
                    "points_redeemed_ytd": 1323,
                    "annual_spending": 4100.00,
                    "membership_since": "2020-12-05T00:00:00",
                    "last_activity": datetime.now().isoformat()
                },
                "preferences": {
                    "favorite_items": ["Chicken Sandwich", "Salad", "Iced Tea"],
                    "dietary_restrictions": ["low-sodium"],
                    "preferred_channels": ["app", "delivery"]
                },
                "purchase_behavior": {
                    "total_orders": 35,
                    "avg_order_value": 195.40,
                    "frequency_score": 6.2,
                    "last_order_date": (datetime.now() - timedelta(days=4)).isoformat()
                },
                "searchable_text": "Carmela Garcia health conscious mom BeeFan tier chicken sandwich delivery app healthy options low sodium mother nanay"
            }
        ]
        
        logger.info(f"Generated {len(customers)} sample customers")
        return customers
    
    def create_sample_stores(self) -> List[Dict]:
        """Create sample store data"""
        logger.info("Generating sample store data...")
        
        stores = [
            {
                "store_id": "store_001",
                "store_name": "SM North EDSA",
                "location": "Quezon City, Metro Manila",
                "address": "SM North EDSA, North Avenue, Quezon City",
                "store_type": "Mall",
                "operating_hours": {
                    "open": "10:00",
                    "close": "22:00",
                    "is_24h": False
                },
                "coordinates": {
                    "lat": 14.6563,
                    "lon": 121.0327
                },
                "features": ["dine-in", "takeout", "delivery", "drive-thru"],
                "status": "active"
            },
            {
                "store_id": "store_002",
                "store_name": "BGC Central Square",
                "location": "Taguig City, Metro Manila",
                "address": "Central Square, Bonifacio Global City, Taguig",
                "store_type": "Standalone",
                "operating_hours": {
                    "open": "06:00",
                    "close": "24:00",
                    "is_24h": False
                },
                "coordinates": {
                    "lat": 14.5548,
                    "lon": 121.0511
                },
                "features": ["dine-in", "takeout", "delivery", "24h-weekend"],
                "status": "active"
            },
            {
                "store_id": "store_003",
                "store_name": "Makati Ayala",
                "location": "Makati City, Metro Manila",
                "address": "Ayala Avenue, Makati City",
                "store_type": "CBD",
                "operating_hours": {
                    "open": "07:00",
                    "close": "23:00",
                    "is_24h": False
                },
                "coordinates": {
                    "lat": 14.5564,
                    "lon": 121.0234
                },
                "features": ["dine-in", "takeout", "delivery"],
                "status": "active"
            },
            {
                "store_id": "store_004",
                "store_name": "UP Town Center",
                "location": "Quezon City, Metro Manila",
                "address": "Katipunan Avenue, UP Town Center, Quezon City",
                "store_type": "Mall",
                "operating_hours": {
                    "open": "10:00",
                    "close": "22:00",
                    "is_24h": False
                },
                "coordinates": {
                    "lat": 14.6497,
                    "lon": 121.0699
                },
                "features": ["dine-in", "takeout", "delivery"],
                "status": "active"
            },
            {
                "store_id": "store_005",
                "store_name": "MOA Complex",
                "location": "Pasay City, Metro Manila",
                "address": "Mall of Asia Complex, Pasay City",
                "store_type": "Mall",
                "operating_hours": {
                    "open": "10:00",
                    "close": "24:00",
                    "is_24h": False
                },
                "coordinates": {
                    "lat": 14.5352,
                    "lon": 120.9754
                },
                "features": ["dine-in", "takeout", "delivery", "seaside-view"],
                "status": "active"
            }
        ]
        
        logger.info(f"Generated {len(stores)} sample stores")
        return stores
    
    def create_sample_inventory(self) -> List[Dict]:
        """Create sample inventory data"""
        logger.info("Generating sample inventory data...")
        
        # Common menu items across all stores
        base_items = [
            {"name": "1 Pc Chickenjoy Solo", "category": "Chickenjoy", "daily_consumption": 15},
            {"name": "6 Pc Chickenjoy Bucket Solo", "category": "Chickenjoy", "daily_consumption": 8},
            {"name": "Yumburger Solo", "category": "Burgers", "daily_consumption": 20},
            {"name": "Cheesy Yumburger Solo", "category": "Burgers", "daily_consumption": 12},
            {"name": "Jolly Spaghetti Solo", "category": "Jolly Spaghetti", "daily_consumption": 18},
            {"name": "Regular Fries", "category": "Fries & Sides", "daily_consumption": 25},
            {"name": "Peach Mango Pie", "category": "Desserts", "daily_consumption": 10},
            {"name": "Iced Coffee Regular", "category": "Beverages", "daily_consumption": 22}
        ]
        
        stores = ["store_001", "store_002", "store_003", "store_004", "store_005"]
        inventory_items = []
        
        for store_id in stores:
            for item in base_items:
                # Randomize stock levels for realism
                import random
                
                max_stock = random.randint(80, 150)
                reorder_point = int(max_stock * 0.3)  # 30% of max stock
                current_stock = random.randint(reorder_point - 10, max_stock)
                
                # Determine status
                if current_stock <= reorder_point * 0.5:
                    status = "Critical"
                elif current_stock <= reorder_point:
                    status = "Low"
                elif current_stock <= reorder_point * 2:
                    status = "Adequate"
                else:
                    status = "Good"
                
                # Calculate predicted stockout
                if item["daily_consumption"] > 0:
                    days_until_stockout = max(0, (current_stock - reorder_point) / item["daily_consumption"])
                    predicted_stockout = datetime.now() + timedelta(days=days_until_stockout)
                else:
                    predicted_stockout = datetime.now() + timedelta(days=30)
                
                inventory_item = {
                    "inventory_id": f"inv_{store_id}_{item['name'].replace(' ', '_').lower()}",
                    "store_id": store_id,
                    "item_name": item["name"],
                    "item_category": item["category"],
                    "current_stock": current_stock,
                    "reorder_point": reorder_point,
                    "max_stock": max_stock,
                    "daily_consumption": item["daily_consumption"],
                    "status": status,
                    "last_restocked": (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat(),
                    "predicted_stockout_date": predicted_stockout.isoformat(),
                    "supplier": "Jollibee Central Kitchen",
                    "unit_cost": random.uniform(15.0, 45.0),
                    "timestamp": datetime.now().isoformat()
                }
                
                inventory_items.append(inventory_item)
        
        logger.info(f"Generated {len(inventory_items)} inventory items across {len(stores)} stores")
        return inventory_items
    
    def verify_setup(self) -> bool:
        """Verify that all data was set up correctly"""
        logger.info("Verifying customer data setup...")
        
        try:
            # Check document counts for all indices
            indices_to_verify = [
                (Config.INDEX_CUSTOMERS, "customers"),
                (Config.INDEX_STORES, "stores"), 
                (Config.INDEX_INVENTORY, "inventory items"),
                (Config.INDEX_TRANSACTIONS, "transactions")
            ]
            
            for index_name, description in indices_to_verify:
                count_query = {"query": {"match_all": {}}, "size": 0}
                response = self.es_client.aggregation_search(index_name, count_query)
                
                if response and response.get('hits', {}).get('total', {}).get('value', 0) > 0:
                    count = response['hits']['total']['value']
                    logger.info(f"✅ {description}: {count} documents")
                else:
                    logger.warning(f"⚠️ {description}: No documents found")
            
            # Test specific customer retrieval
            test_customer = self.es_client.get_document(Config.INDEX_CUSTOMERS, "mike001")
            if test_customer:
                logger.info(f"✅ Test customer '{test_customer['personal_info']['name']}' found with {test_customer['loyalty_profile']['total_points']} points")
            else:
                logger.error("❌ Test customer 'mike001' not found")
                return False
            
            # Test specific store retrieval  
            test_store = self.es_client.get_document(Config.INDEX_STORES, "store_001")
            if test_store:
                logger.info(f"✅ Test store '{test_store['store_name']}' found")
            else:
                logger.error("❌ Test store 'store_001' not found")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}")
            return False
    
    def run_setup(self) -> bool:
        """Run complete customer data setup"""
        logger.info("🚀 Starting Customer & Store Data Setup")
        logger.info("=" * 60)
        
        try:
            # Create all indices
            indices_created = all([
                self.create_customer_index(),
                self.create_transactions_index(),
                self.create_stores_index(),
                self.create_inventory_index()
            ])
            
            if not indices_created:
                logger.error("Failed to create one or more indices")
                return False
            
            # Create and index sample data
            customers = self.create_sample_customers()
            stores = self.create_sample_stores()
            inventory = self.create_sample_inventory()
            
            # Bulk index all data
            data_indexed = all([
                self.es_client.bulk_index(Config.INDEX_CUSTOMERS, customers),
                self.es_client.bulk_index(Config.INDEX_STORES, stores),
                self.es_client.bulk_index(Config.INDEX_INVENTORY, inventory)
            ])
            
            if not data_indexed:
                logger.error("Failed to index one or more data sets")
                return False
            
            # Wait for indexing
            import time
            logger.info("⏳ Waiting for indexing...")
            time.sleep(3)
            
            # Refresh indices
            self.es_client.refresh_index([
                Config.INDEX_CUSTOMERS,
                Config.INDEX_STORES,
                Config.INDEX_INVENTORY,
                Config.INDEX_TRANSACTIONS
            ])
            
            # Verify setup
            if not self.verify_setup():
                logger.error("Setup verification failed")
                return False
            
            logger.info("✅ Customer & Store data setup completed successfully!")
            logger.info("🎉 Ready for real-time analytics and transactions!")
            
            return True
            
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False

def main():
    """Main setup function"""
    try:
        setup = JollibeeCustomerSetup()
        success = setup.run_setup()
        
        if success:
            print("\n🚀 Next Steps:")
            print("1. Start the main application: python app.py")
            print("2. Test point redemption with sample customers")
            print("3. Create transactions and see real-time updates")
            
            # Show what was created
            print("\n📊 Data Summary:")
            print("   • 5 sample customers (mike001, zander001, john001, melvin001, carms001)")
            print("   • 5 store locations (store_001 to store_005)")
            print("   • 40 inventory items across all stores")
            print("   • Ready for real-time transactions")
        else:
            print("\n❌ Customer setup failed. Check logs for details.")
            
        return success
        
    except Exception as e:
        logger.error(f"Setup error: {str(e)}")
        return False

def debug_data_check():
    """Debug function to manually check if data exists"""
    print("🔍 Debug: Checking if data was ingested...")
    
    try:
        from config import Config
        from elasticsearch_client import ElasticsearchClient
        
        es_client = ElasticsearchClient()
        
        # Check each index
        indices = [
            (Config.INDEX_CUSTOMERS, ["mike001", "zander001"]),
            (Config.INDEX_STORES, ["store_001", "store_002"]),
            (Config.INDEX_INVENTORY, None)
        ]
        
        for index_name, sample_ids in indices:
            print(f"\n📋 Checking {index_name}:")
            
            # Get total count
            count_query = {"query": {"match_all": {}}, "size": 0}
            response = es_client.aggregation_search(index_name, count_query)
            
            if response and response.get('hits', {}).get('total', {}).get('value', 0) > 0:
                count = response['hits']['total']['value']
                print(f"   ✅ Total documents: {count}")
                
                # Check specific IDs if provided
                if sample_ids:
                    for doc_id in sample_ids:
                        doc = es_client.get_document(index_name, doc_id)
                        if doc:
                            if 'personal_info' in doc:
                                print(f"   ✅ {doc_id}: {doc['personal_info']['name']}")
                            elif 'store_name' in doc:
                                print(f"   ✅ {doc_id}: {doc['store_name']}")
                            else:
                                print(f"   ✅ {doc_id}: Document exists")
                        else:
                            print(f"   ❌ {doc_id}: Not found")
            else:
                print(f"   ❌ No documents found in {index_name}")
                
    except Exception as e:
        print(f"❌ Debug check failed: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        debug_data_check()
    else:
        success = main()
        exit(0 if success else 1)
