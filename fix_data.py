#!/usr/bin/env python3
"""
Fix script for inventory data issues
"""

import logging
from config import Config
from elasticsearch_client import ElasticsearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_inventory_data():
    """Fix inventory data by recreating it properly"""
    print("🔧 Fixing Inventory Data Issues")
    print("=" * 50)
    
    try:
        es_client = ElasticsearchClient()
        
        # Check current inventory count
        count_query = {"query": {"match_all": {}}, "size": 0}
        response = es_client.aggregation_search(Config.INDEX_INVENTORY, count_query)
        
        current_count = 0
        if response and response.get('hits', {}).get('total', {}).get('value', 0) >= 0:
            current_count = response['hits']['total']['value']
        
        print(f"📊 Current inventory count: {current_count}")
        
        if current_count >= 40:
            print("✅ Inventory data looks good, no fix needed")
            return True
        
        print("🔄 Regenerating inventory data...")
        
        # Import the customer setup to regenerate inventory
        from setup.customer_setup import JollibeeCustomerSetup
        
        setup = JollibeeCustomerSetup()
        
        # Generate fresh inventory data
        inventory_items = setup.create_sample_inventory()
        print(f"📦 Generated {len(inventory_items)} inventory items")
        
        # Clear existing inventory and re-index
        print("🗑️ Clearing existing inventory...")
        
        # Delete and recreate index
        if not setup.create_inventory_index():
            print("❌ Failed to recreate inventory index")
            return False
        
        # Bulk index new data
        print("📥 Indexing new inventory data...")
        if not es_client.bulk_index(Config.INDEX_INVENTORY, inventory_items):
            print("❌ Failed to index inventory data")
            return False
        
        # Refresh index
        es_client.refresh_index(Config.INDEX_INVENTORY)
        
        # Verify the fix
        import time
        time.sleep(2)
        
        response = es_client.aggregation_search(Config.INDEX_INVENTORY, count_query)
        new_count = 0
        if response and response.get('hits', {}).get('total', {}).get('value', 0) >= 0:
            new_count = response['hits']['total']['value']
        
        print(f"📊 New inventory count: {new_count}")
        
        if new_count >= 40:
            print("✅ Inventory data fixed successfully!")
            
            # Show sample items
            sample_query = {"query": {"match_all": {}}, "size": 5}
            sample_response = es_client.aggregation_search(Config.INDEX_INVENTORY, sample_query)
            
            if sample_response and sample_response.get('hits', {}).get('hits'):
                print("\n📦 Sample inventory items:")
                for hit in sample_response['hits']['hits']:
                    item = hit['_source']
                    print(f"   • {item['item_name']} at {item['store_id']}: {item['current_stock']} units ({item['status']})")
            
            return True
        else:
            print("❌ Inventory fix failed - count is still low")
            return False
            
    except Exception as e:
        print(f"❌ Inventory fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_price_issues():
    """Check for price parsing issues in menu data"""
    print("\n🔍 Checking Menu Price Issues")
    print("=" * 40)
    
    try:
        es_client = ElasticsearchClient()
        
        # Find items with suspicious prices
        price_query = {
            "query": {
                "range": {
                    "price": {"gte": 10000}  # Prices over ₱10,000 are suspicious
                }
            },
            "size": 10,
            "_source": ["name", "price", "category"]
        }
        
        response = es_client.aggregation_search(Config.INDEX_MENU, price_query)
        
        if response and response.get('hits', {}).get('hits'):
            print(f"⚠️  Found {len(response['hits']['hits'])} items with suspicious prices:")
            
            for hit in response['hits']['hits']:
                item = hit['_source']
                print(f"   • {item['name']}: ₱{item['price']:,.0f} ({item['category']})")
            
            print("\n💡 These prices were likely parsed incorrectly from the website.")
            print("   The system will fall back to static menu data for better accuracy.")
            return False
        else:
            print("✅ No suspicious prices found in menu data")
            return True
            
    except Exception as e:
        print(f"❌ Price check failed: {str(e)}")
        return False

def main():
    """Main fix function"""
    print("🛠️  Jollibee System Data Fix")
    print("=" * 60)
    
    try:
        # Fix 1: Inventory data
        inventory_fixed = fix_inventory_data()
        
        # Fix 2: Check price issues
        prices_ok = check_price_issues()
        
        # Summary
        print("\n" + "=" * 60)
        print("📋 Fix Summary:")
        print(f"   Inventory Data: {'✅ FIXED' if inventory_fixed else '❌ NEEDS ATTENTION'}")
        print(f"   Menu Prices: {'✅ GOOD' if prices_ok else '⚠️ SOME ISSUES'}")
        
        if inventory_fixed and prices_ok:
            print("\n🎉 All issues fixed! Run debug_data.py to verify.")
        elif inventory_fixed:
            print("\n✅ Inventory fixed! Some menu prices may be inaccurate but system will work.")
        else:
            print("\n⚠️  Some issues remain. You may need to run setup_all.py again.")
        
        print("\n🚀 Next steps:")
        print("   1. Run: python debug_data.py")
        print("   2. If all good: python app.py")
        
        return inventory_fixed
        
    except Exception as e:
        print(f"❌ Fix script failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
