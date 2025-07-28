#!/usr/bin/env python3
"""
Debug script to check Elasticsearch data ingestion status
"""

import logging
from config import Config
from elasticsearch_client import ElasticsearchClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_data_ingestion():
    """Check if all data has been properly ingested"""
    print("🔍 Checking Elasticsearch Data Ingestion Status")
    print("=" * 60)
    
    try:
        es_client = ElasticsearchClient()
        
        # Test connection first
        health = es_client.health_check()
        if health["status"] != "healthy":
            print("❌ Elasticsearch connection failed!")
            return False
        
        print(f"✅ Connected to Elasticsearch: {health.get('cluster_name', 'unknown')}")
        print()
        
        # Check each index
        indices_to_check = [
            {
                "index": Config.INDEX_MENU,
                "name": "Menu Items",
                "sample_docs": [],  # Just check count, items have random UUIDs
                "expected_min": 50
            },
            {
                "index": Config.INDEX_CUSTOMERS,
                "name": "Customers",
                "sample_docs": ["mike001", "zander001", "john001", "melvin001", "carms001"],
                "expected_min": 5
            },
            {
                "index": Config.INDEX_STORES,
                "name": "Stores",
                "sample_docs": ["store_001", "store_002", "store_003", "store_004", "store_005"],
                "expected_min": 5
            },
            {
                "index": Config.INDEX_INVENTORY,
                "name": "Inventory Items",
                "sample_docs": [],  # Just check count, has complex IDs
                "expected_min": 30
            },
            {
                "index": Config.INDEX_TRANSACTIONS,
                "name": "Transactions",
                "sample_docs": [],
                "expected_min": 0  # May be empty initially
            }
        ]
        
        all_good = True
        
        for index_info in indices_to_check:
            index_name = index_info["index"]
            friendly_name = index_info["name"]
            sample_docs = index_info["sample_docs"]
            expected_min = index_info["expected_min"]
            
            print(f"📋 Checking {friendly_name} ({index_name}):")
            
            # Get total document count
            count_query = {"query": {"match_all": {}}, "size": 0}
            response = es_client.aggregation_search(index_name, count_query)
            
            if response and response.get('hits', {}).get('total', {}).get('value', 0) >= 0:
                count = response['hits']['total']['value']
                
                if count >= expected_min:
                    print(f"   ✅ Document count: {count} (expected minimum: {expected_min})")
                else:
                    print(f"   ⚠️  Document count: {count} (expected minimum: {expected_min})")
                    if expected_min > 0:
                        all_good = False
                
                # Check sample documents
                if sample_docs:
                    for doc_id in sample_docs:
                        if doc_id.endswith("_"):  # Prefix search
                            # Use search instead of direct get
                            search_query = {
                                "query": {"prefix": {"_id": doc_id}},
                                "size": 1
                            }
                            search_response = es_client.aggregation_search(index_name, search_query)
                            
                            if (search_response and 
                                search_response.get('hits', {}).get('hits')):
                                found_doc = search_response['hits']['hits'][0]
                                print(f"   ✅ Sample found: {found_doc['_id']}")
                            else:
                                print(f"   ❌ No documents found with prefix: {doc_id}")
                                if expected_min > 0:
                                    all_good = False
                        else:
                            # Direct document get
                            doc = es_client.get_document(index_name, doc_id)
                            if doc:
                                if 'personal_info' in doc:
                                    print(f"   ✅ {doc_id}: {doc['personal_info']['name']}")
                                elif 'store_name' in doc:
                                    print(f"   ✅ {doc_id}: {doc['store_name']}")
                                elif 'name' in doc:
                                    print(f"   ✅ {doc_id}: {doc['name']}")
                                else:
                                    print(f"   ✅ {doc_id}: Document exists")
                            else:
                                print(f"   ❌ {doc_id}: Not found")
                                if expected_min > 0:
                                    all_good = False
                else:
                    # For indices without specific sample docs, show a few sample items
                    if count > 0:
                        sample_query = {"query": {"match_all": {}}, "size": 3}
                        sample_response = es_client.aggregation_search(index_name, sample_query)
                        
                        if sample_response and sample_response.get('hits', {}).get('hits'):
                            print(f"   📄 Sample items:")
                            for hit in sample_response['hits']['hits'][:3]:
                                doc = hit['_source']
                                doc_id = hit['_id']
                                
                                if 'name' in doc:
                                    print(f"      • {doc_id}: {doc['name']}")
                                elif 'item_name' in doc:
                                    print(f"      • {doc_id}: {doc['item_name']} (stock: {doc.get('current_stock', 'N/A')})")
                                else:
                                    print(f"      • {doc_id}: Document exists")
            else:
                print(f"   ❌ Could not retrieve data from {index_name}")
                if expected_min > 0:
                    all_good = False
            
            print()
        
        # Overall status
        if all_good:
            print("🎉 All data appears to be properly ingested!")
            print("\n✅ Ready to run the application:")
            print("   python app.py")
        else:
            print("⚠️  Some data may be missing. Try running setup again:")
            print("   python setup_all.py")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error checking data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_specific_customer(customer_id="mike001"):
    """Check a specific customer in detail"""
    print(f"\n🔍 Detailed Customer Check: {customer_id}")
    print("-" * 40)
    
    try:
        es_client = ElasticsearchClient()
        customer = es_client.get_document(Config.INDEX_CUSTOMERS, customer_id)
        
        if customer:
            print(f"✅ Customer found: {customer['personal_info']['name']}")
            print(f"   Email: {customer['personal_info']['email']}")
            print(f"   Tier: {customer['loyalty_profile']['tier']}")
            print(f"   Points: {customer['loyalty_profile']['total_points']}")
            print(f"   Annual Spending: ₱{customer['loyalty_profile']['annual_spending']}")
            print(f"   Favorite Items: {', '.join(customer['preferences']['favorite_items'])}")
            return True
        else:
            print(f"❌ Customer {customer_id} not found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking customer: {str(e)}")
        return False

def test_semantic_search():
    """Test semantic search functionality"""
    print(f"\n🔍 Testing Semantic Search")
    print("-" * 40)
    
    try:
        from jollibee_service import JollibeeService
        
        service = JollibeeService()
        
        test_queries = [
            "family meal",
            "budget food",
            "dessert"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = service.search_menu(query)
            
            if results:
                print(f"   ✅ Found {len(results)} results:")
                for i, item in enumerate(results[:3], 1):
                    print(f"      {i}. {item['name']} - ₱{item['price']}")
            else:
                print(f"   ❌ No results found")
                
        return True
        
    except Exception as e:
        print(f"❌ Semantic search test failed: {str(e)}")
        return False

def main():
    """Main debug function"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "customer":
            customer_id = sys.argv[2] if len(sys.argv) > 2 else "mike001"
            check_specific_customer(customer_id)
        elif sys.argv[1] == "search":
            test_semantic_search()
        else:
            print("Usage:")
            print("  python debug_data.py           # Check all data")
            print("  python debug_data.py customer  # Check specific customer")
            print("  python debug_data.py search    # Test semantic search")
    else:
        check_data_ingestion()

if __name__ == "__main__":
    main()
