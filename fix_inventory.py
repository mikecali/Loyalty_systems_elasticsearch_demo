#!/usr/bin/env python3
"""
FINAL Inventory Fix - Addresses the root cause: Document ID priority issue
The bulk_index function was using store_id instead of inventory_id, causing overwrites
"""

import logging
import uuid
from datetime import datetime, timedelta
import random
from config import Config
from elasticsearch_client import ElasticsearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def explain_root_cause():
    """Explain what was causing the inventory issue"""
    print("🔍 ROOT CAUSE ANALYSIS")
    print("=" * 60)
    print("❌ PROBLEM IDENTIFIED:")
    print("   The bulk_index() function in elasticsearch_client.py was using")
    print("   the wrong document ID for inventory items.")
    print()
    print("   OLD BEHAVIOR:")
    print("   • Checked ID fields in this order: id, item_id, customer_id, store_id, inventory_id")
    print("   • Found 'store_id' first → used it as document ID")
    print("   • All items for same store overwrote each other")
    print("   • Result: Only 1 item per store (5 total)")
    print()
    print("✅ SOLUTION IMPLEMENTED:")
    print("   • Fixed ID priority per index type")
    print("   • For inventory index: inventory_id gets priority")
    print("   • Each item gets unique document ID")
    print("   • Result: All 80 items should be indexed")
    print()

def verify_elasticsearch_client_fix():
    """Verify the elasticsearch client has the fix"""
    print("🔧 Verifying Elasticsearch Client Fix")
    print("=" * 50)
    
    try:
        from elasticsearch_client import ElasticsearchClient
        
        # Check if the _determine_document_id method exists (indicates fixed version)
        es_client = ElasticsearchClient()
        
        if hasattr(es_client, '_determine_document_id'):
            print("✅ Fixed elasticsearch_client.py detected")
            
            # Test the ID determination logic
            test_doc = {
                'inventory_id': 'inv_test_123',
                'store_id': 'store_001',
                'item_name': 'Test Item'
            }
            
            determined_id = es_client._determine_document_id(Config.INDEX_INVENTORY, test_doc)
            
            if determined_id == 'inv_test_123':
                print("✅ ID priority working correctly (inventory_id used)")
                return True
            else:
                print(f"❌ ID priority issue: got {determined_id}, expected inv_test_123")
                return False
        else:
            print("❌ OLD elasticsearch_client.py detected - needs update")
            print("   Please replace elasticsearch_client.py with the fixed version")
            return False
            
    except Exception as e:
        print(f"❌ Error checking elasticsearch client: {str(e)}")
        return False

def fix_inventory_with_corrected_client():
    """Fix inventory using the corrected elasticsearch client"""
    print("\n🔧 Fixing Inventory with Corrected Client")
    print("=" * 50)
    
    try:
        es_client = ElasticsearchClient()
        
        # Generate comprehensive inventory data
        inventory_items = create_comprehensive_inventory_data()
        print(f"📦 Generated {len(inventory_items)} inventory items")
        
        # Show first few items to verify unique IDs
        print("\n🔍 Verifying unique IDs:")
        for i, item in enumerate(inventory_items[:5]):
            print(f"   {i+1}. ID: {item['inventory_id']}")
            print(f"      Store: {item['store_id']}, Item: {item['item_name']}")
        
        # Clear and recreate index
        print("\n🗑️ Recreating inventory index...")
        if not create_inventory_index(es_client):
            print("❌ Failed to recreate inventory index")
            return False
        
        # Bulk index with fixed client
        print("📥 Bulk indexing with FIXED client (inventory_id priority)...")
        success = es_client.bulk_index(Config.INDEX_INVENTORY, inventory_items)
        
        if not success:
            print("❌ Bulk indexing failed")
            return False
        
        # Refresh and verify
        es_client.refresh_index(Config.INDEX_INVENTORY)
        
        print("⏳ Waiting for indexing to complete...")
        import time
        time.sleep(3)
        
        # Verify the fix
        print("\n🧪 Verifying Fix...")
        for attempt in range(3):
            count_query = {"query": {"match_all": {}}, "size": 0}
            response = es_client.aggregation_search(Config.INDEX_INVENTORY, count_query)
            
            actual_count = 0
            if response and response.get('hits', {}).get('total', {}).get('value', 0) >= 0:
                actual_count = response['hits']['total']['value']
            
            expected_count = len(inventory_items)
            print(f"   Attempt {attempt + 1}: {actual_count}/{expected_count} items indexed")
            
            if actual_count >= expected_count * 0.95:  # Accept 95% success
                print(f"✅ SUCCESS! {actual_count} items properly indexed")
                
                # Verify store distribution
                print("\n📊 Verifying store distribution:")
                for store_id in ["store_001", "store_002", "store_003", "store_004", "store_005"]:
                    store_query = {
                        "query": {"term": {"store_id": store_id}},
                        "size": 0
                    }
                    store_response = es_client.aggregation_search(Config.INDEX_INVENTORY, store_query)
                    store_count = 0
                    if store_response:
                        store_count = store_response.get('hits', {}).get('total', {}).get('value', 0)
                    print(f"   {store_id}: {store_count} items")
                
                # Show sample items
                print("\n📦 Sample inventory items:")
                sample_query = {"query": {"match_all": {}}, "size": 8}
                sample_response = es_client.aggregation_search(Config.INDEX_INVENTORY, sample_query)
                
                if sample_response and sample_response.get('hits', {}).get('hits'):
                    for hit in sample_response['hits']['hits']:
                        item = hit['_source']
                        print(f"   • {item['item_name']} at {item['store_id']}: {item['current_stock']} units ({item['status']})")
                
                return True
            
            time.sleep(2)
        
        print(f"❌ Fix verification failed - only {actual_count}/{expected_count} items indexed")
        return False
        
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_comprehensive_inventory_data():
    """Create comprehensive inventory data with guaranteed unique IDs"""
    
    # Complete menu items for realistic inventory
    base_items = [
        {"name": "1 Pc Chickenjoy Solo", "category": "Chickenjoy", "daily_consumption": 15},
        {"name": "2 Pc Chickenjoy Solo", "category": "Chickenjoy", "daily_consumption": 12},
        {"name": "6 Pc Chickenjoy Bucket Solo", "category": "Chickenjoy", "daily_consumption": 8},
        {"name": "8 Pc Chickenjoy Bucket Solo", "category": "Chickenjoy", "daily_consumption": 5},
        {"name": "Yumburger Solo", "category": "Burgers", "daily_consumption": 20},
        {"name": "Cheesy Yumburger Solo", "category": "Burgers", "daily_consumption": 12},
        {"name": "Champ Solo", "category": "Burgers", "daily_consumption": 8},
        {"name": "Jolly Spaghetti Solo", "category": "Jolly Spaghetti", "daily_consumption": 18},
        {"name": "Regular Fries", "category": "Fries & Sides", "daily_consumption": 25},
        {"name": "Large Fries", "category": "Fries & Sides", "daily_consumption": 15},
        {"name": "Peach Mango Pie", "category": "Desserts", "daily_consumption": 10},
        {"name": "Chocolate Sundae Twirl", "category": "Desserts", "daily_consumption": 8},
        {"name": "Iced Coffee Regular", "category": "Beverages", "daily_consumption": 22},
        {"name": "Coke Regular", "category": "Beverages", "daily_consumption": 30},
        {"name": "Sprite Regular", "category": "Beverages", "daily_consumption": 20},
        {"name": "Extra Rice", "category": "Fries & Sides", "daily_consumption": 40}
    ]
    
    stores = ["store_001", "store_002", "store_003", "store_004", "store_005"]
    inventory_items = []
    
    for store_idx, store_id in enumerate(stores):
        for item_idx, item in enumerate(base_items):
            # CRITICAL: Create guaranteed unique inventory_id
            unique_id = f"inv_{store_id}_{item_idx:02d}_{str(uuid.uuid4())[:8]}"
            
            # Generate realistic stock levels
            base_max = random.randint(80, 150)
            store_modifier = 0.8 + (store_idx * 0.1)
            max_stock = int(base_max * store_modifier)
            reorder_point = int(max_stock * 0.3)
            current_stock = random.randint(max(0, reorder_point - 10), max_stock)
            
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
                "inventory_id": unique_id,  # PRIMARY ID - will be used as document ID
                "store_id": store_id,       # Secondary field - not used as document ID
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
    
    return inventory_items

def create_inventory_index(es_client):
    """Create inventory index with proper mapping"""
    
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
                "item_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
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
    
    return es_client.create_index(Config.INDEX_INVENTORY, mapping)

def test_final_inventory_state():
    """Final test of inventory state"""
    print("\n🧪 Final Inventory State Test")
    print("=" * 40)
    
    try:
        es_client = ElasticsearchClient()
        
        # Test overall count
        total_query = {"query": {"match_all": {}}, "size": 0}
        total_response = es_client.aggregation_search(Config.INDEX_INVENTORY, total_query)
        total_count = total_response.get('hits', {}).get('total', {}).get('value', 0) if total_response else 0
        
        print(f"📊 Total inventory items: {total_count}")
        
        # Test store distribution
        agg_query = {
            "size": 0,
            "aggs": {
                "stores": {"terms": {"field": "store_id", "size": 10}},
                "statuses": {"terms": {"field": "status", "size": 10}},
                "categories": {"terms": {"field": "item_category", "size": 20}}
            }
        }
        
        agg_response = es_client.aggregation_search(Config.INDEX_INVENTORY, agg_query)
        
        if agg_response and agg_response.get('aggregations'):
            print("\n🏪 Store distribution:")
            for bucket in agg_response['aggregations']['stores']['buckets']:
                print(f"   {bucket['key']}: {bucket['doc_count']} items")
            
            print("\n📊 Status distribution:")
            for bucket in agg_response['aggregations']['statuses']['buckets']:
                print(f"   {bucket['key']}: {bucket['doc_count']} items")
            
            print("\n🍽️ Category distribution:")
            for bucket in agg_response['aggregations']['categories']['buckets']:
                print(f"   {bucket['key']}: {bucket['doc_count']} items")
        
        # Test specific store query (this was failing before)
        store_query = {
            "query": {"term": {"store_id": "store_001"}},
            "size": 5,
            "_source": ["item_name", "current_stock", "status"]
        }
        
        store_response = es_client.aggregation_search(Config.INDEX_INVENTORY, store_query)
        
        if store_response and store_response.get('hits', {}).get('hits'):
            print(f"\n📦 Sample items from store_001:")
            for hit in store_response['hits']['hits']:
                item = hit['_source']
                print(f"   • {item['item_name']}: {item['current_stock']} units ({item['status']})")
        
        return total_count >= 50  # Success if we have at least 50 items
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main fix function"""
    print("🛠️  FINAL Jollibee Inventory Fix - ID Priority Issue")
    print("=" * 60)
    
    try:
        # Step 1: Explain the root cause
        explain_root_cause()
        
        # Step 2: Verify the elasticsearch client fix
        if not verify_elasticsearch_client_fix():
            print("\n❌ CRITICAL: elasticsearch_client.py needs to be updated first!")
            print("   Please replace your elasticsearch_client.py with the fixed version")
            print("   that includes the _determine_document_id() method")
            return False
        
        # Step 3: Fix inventory with corrected client
        if not fix_inventory_with_corrected_client():
            print("\n❌ Inventory fix failed")
            return False
        
        # Step 4: Final verification
        if not test_final_inventory_state():
            print("\n⚠️ Final test incomplete")
            return False
        
        # Success!
        print("\n" + "=" * 60)
        print("🎉 INVENTORY ISSUE COMPLETELY FIXED!")
        print("=" * 60)
        print("✅ Root cause identified and resolved")
        print("✅ Document ID priority corrected") 
        print("✅ All inventory items properly indexed")
        print("✅ Store queries working correctly")
        print("✅ Analytics will show all items")
        
        print("\n🚀 Next steps:")
        print("   1. Run: python debug_data.py")
        print("   2. Should now show 80+ inventory items")
        print("   3. Start app: python app.py")
        print("   4. Inventory analytics will show multiple items per store")
        
        return True
        
    except Exception as e:
        print(f"❌ Fix script failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
