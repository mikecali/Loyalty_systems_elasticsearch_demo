#!/usr/bin/env python3
"""
Complete Jollibee BeeLoyalty System Setup
Initializes all Elasticsearch indices and sample data
"""

import sys
import os
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup.log')
    ]
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print setup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🍯 JOLLIBEE BEELOYALTY SYSTEM SETUP                   ║
║                                                              ║
║     Complete Elasticsearch + ELSER Platform Setup           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)
    print(f"🕐 Setup Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 66)

def check_environment():
    """Check if environment is properly configured"""
    logger.info("🔍 Checking environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        logger.error("❌ .env file not found!")
        logger.info("📋 Please copy .env.example to .env and configure your settings")
        return False
    
    # Try to load configuration
    try:
        from config import Config
        Config.validate()
        logger.info("✅ Environment configuration is valid")
        return True
    except Exception as e:
        logger.error(f"❌ Environment configuration error: {str(e)}")
        return False

def test_elasticsearch_connection():
    """Test Elasticsearch connection"""
    logger.info("🔗 Testing Elasticsearch connection...")
    
    try:
        from elasticsearch_client import ElasticsearchClient
        
        es_client = ElasticsearchClient()
        health = es_client.health_check()
        
        if health["status"] == "healthy":
            logger.info("✅ Elasticsearch connection successful")
            logger.info(f"   Cluster: {health.get('cluster_name', 'unknown')}")
            logger.info(f"   Status: {health.get('cluster_status', 'unknown')}")
            return True
        else:
            logger.error("❌ Elasticsearch cluster is not healthy")
            return False
            
    except Exception as e:
        logger.error(f"❌ Elasticsearch connection failed: {str(e)}")
        return False

def setup_elser_pipeline():
    """Setup ELSER pipeline if not exists"""
    logger.info("🧠 Setting up ELSER pipeline...")
    
    try:
        from elasticsearch_client import ElasticsearchClient
        from config import Config
        
        es_client = ElasticsearchClient()
        
        # Check if pipeline exists
        response = es_client.request("GET", f"/_ingest/pipeline/{Config.ELSER_PIPELINE_NAME}")
        
        if response and response.status_code == 200:
            logger.info("✅ ELSER pipeline already exists")
            return True
        
        # Create ELSER pipeline
        pipeline_config = {
            "processors": [
                {
                    "inference": {
                        "model_id": Config.ELSER_MODEL_ID,
                        "target_field": "ml",
                        "field_map": {
                            "searchable_text": "text_field"
                        },
                        "inference_config": {
                            "text_expansion": {
                                "results_field": "tokens"
                            }
                        }
                    }
                }
            ]
        }
        
        response = es_client.request("PUT", f"/_ingest/pipeline/{Config.ELSER_PIPELINE_NAME}", pipeline_config)
        
        if response and response.status_code == 200:
            logger.info("✅ ELSER pipeline created successfully")
            return True
        else:
            logger.error(f"❌ Failed to create ELSER pipeline: {response.status_code if response else 'No response'}")
            return False
            
    except Exception as e:
        logger.error(f"❌ ELSER pipeline setup failed: {str(e)}")
        return False

def run_menu_setup():
    """Run menu data setup"""
    logger.info("📋 Setting up menu data with ELSER...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'setup'))
        from menu_setup import JollibeeMenuSetup
        
        menu_setup = JollibeeMenuSetup()
        success = menu_setup.run_setup()
        
        if success:
            logger.info("✅ Menu setup completed successfully")
            return True
        else:
            logger.error("❌ Menu setup failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Menu setup error: {str(e)}")
        return False

def run_customer_setup():
    """Run customer and store data setup"""
    logger.info("👥 Setting up customer and store data...")
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'setup'))
        from customer_setup import JollibeeCustomerSetup
        
        customer_setup = JollibeeCustomerSetup()
        success = customer_setup.run_setup()
        
        if success:
            logger.info("✅ Customer and store setup completed successfully")
            return True
        else:
            logger.error("❌ Customer and store setup failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Customer setup error: {str(e)}")
        return False

def verify_complete_setup():
    """Verify that the complete setup is working"""
    logger.info("🧪 Verifying complete setup...")
    
    try:
        from jollibee_service import JollibeeService
        from config import Config
        
        service = JollibeeService()
        
        # Test index existence and document counts
        indices_to_check = [
            (Config.INDEX_MENU, "menu items"),
            (Config.INDEX_CUSTOMERS, "customers"),
            (Config.INDEX_STORES, "stores"),
            (Config.INDEX_INVENTORY, "inventory items")
        ]
        
        for index_name, description in indices_to_check:
            count_query = {"query": {"match_all": {}}, "size": 0}
            response = service.es_client.aggregation_search(index_name, count_query)
            
            if response and response.get('hits', {}).get('total', {}).get('value', 0) > 0:
                count = response['hits']['total']['value']
                logger.info(f"✅ {description}: {count} documents indexed")
            else:
                logger.error(f"❌ {description}: No documents found in {index_name}")
                return False
        
        # Test customer retrieval
        customer = service.get_customer("mike001")
        if not customer:
            logger.error("❌ Customer retrieval test failed")
            return False
        
        # Test store retrieval
        store = service.es_client.get_document(Config.INDEX_STORES, "store_001")
        if not store:
            logger.error("❌ Store retrieval test failed")
            return False
        
        # Test menu search
        menu_results = service.search_menu("family meal")
        if not menu_results:
            logger.error("❌ Menu search test failed")
            return False
        
        # Test recommendations
        recommendations = service.get_customer_recommendations("mike001")
        if not recommendations:
            logger.error("❌ Recommendations test failed")
            return False
        
        logger.info("✅ All verification tests passed")
        logger.info(f"   Customer: {customer['personal_info']['name']}")
        logger.info(f"   Store: {store['store_name']}")
        logger.info(f"   Menu search results: {len(menu_results)}")
        logger.info(f"   Recommendations: {len(recommendations)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def print_success_summary():
    """Print success summary with next steps"""
    summary = """
✅ SETUP COMPLETED SUCCESSFULLY!

🎉 Your Jollibee BeeLoyalty System is ready!

📊 What's been set up:
   • Elasticsearch indices with ELSER semantic search
   • Real Jollibee menu data (200+ items)
   • Sample customers with loyalty profiles
   • Store locations and inventory data
   • Real-time analytics infrastructure

🚀 Next Steps:
   1. Start the application:
      python app.py

   2. Open your browser:
      http://localhost:5000

   3. Try the demo features:
      • Semantic menu search
      • AI-powered recommendations
      • Real-time analytics
      • Bulk order simulation

🔍 Test Semantic Search:
   • "family meal crispy chicken" → Family buckets
   • "budget student food" → Affordable options
   • "sweet dessert ice cream" → Sundaes and pies

📈 Demo Scenarios:
   • Select customer profiles (Mike, Zander, Melvin, etc.)
   • Run bulk order simulations
   • Watch real-time analytics update

📚 Documentation:
   • README.md - Complete setup guide
   • /demo - Interactive demo guide
   
Happy building! 🍯
"""
    print(summary)

def main():
    """Main setup function"""
    try:
        print_banner()
        
        # Step 1: Check environment
        if not check_environment():
            logger.error("Environment check failed. Setup aborted.")
            return False
        
        # Step 2: Test Elasticsearch connection
        if not test_elasticsearch_connection():
            logger.error("Elasticsearch connection failed. Setup aborted.")
            return False
        
        # Step 3: Setup ELSER pipeline
        if not setup_elser_pipeline():
            logger.error("ELSER pipeline setup failed. Setup aborted.")
            return False
        
        # Step 4: Setup menu data
        if not run_menu_setup():
            logger.error("Menu setup failed. Setup aborted.")
            return False
        
        # Step 5: Setup customer and store data
        if not run_customer_setup():
            logger.error("Customer setup failed. Setup aborted.")
            return False
        
        # Step 6: Wait for indexing to complete
        logger.info("⏳ Waiting for final indexing to complete...")
        time.sleep(5)
        
        # Step 7: Verify complete setup
        if not verify_complete_setup():
            logger.error("Setup verification failed.")
            return False
        
        # Step 8: Print success summary
        print_success_summary()
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Setup interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("🎉 Setup completed successfully!")
        exit(0)
    else:
        logger.error("❌ Setup failed. Check logs for details.")
        exit(1)
