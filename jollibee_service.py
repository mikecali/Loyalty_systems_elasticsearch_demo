"""
Optimized Jollibee BeeLoyalty System - Core Business Logic Service
Performance optimized version with bulk operations and efficient data handling
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from elasticsearch_client import ElasticsearchClient
from config import Config

logger = logging.getLogger(__name__)

class JollibeeService:
    """Optimized core business logic service for Jollibee BeeLoyalty system"""
    
    def __init__(self):
        """Initialize service with Elasticsearch client"""
        self.es_client = ElasticsearchClient()
        logger.info("Initialized Jollibee Service")
    
    # Customer Management (unchanged - these are already optimized)
    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer profile by ID"""
        customer = self.es_client.get_document(Config.INDEX_CUSTOMERS, customer_id)
        if customer:
            logger.info(f"Retrieved customer: {customer['personal_info']['name']}")
        return customer
    
    def get_customer_recommendations(self, customer_id: str, limit: int = 8) -> List[Dict]:
        """Get personalized menu recommendations for customer"""
        customer = self.get_customer(customer_id)
        if not customer:
            return []
        
        # Build semantic query from customer preferences
        favorite_items = customer.get('preferences', {}).get('favorite_items', [])
        search_text = " ".join(favorite_items)
        
        if not search_text.strip():
            search_text = "popular bestseller recommended"
        
        # Perform semantic search
        results = self.es_client.semantic_search(
            Config.INDEX_MENU,
            search_text,
            size=limit,
            source_fields=["name", "category", "price", "description", "points_value", "is_new", "is_bestseller"]
        )
        
        recommendations = []
        for hit in results.get('hits', {}).get('hits', []):
            item = hit['_source']
            recommendations.append({
                "name": item['name'],
                "category": item['category'],
                "price": item['price'],
                "description": item['description'],
                "points_value": item['points_value'],
                "is_new": item.get('is_new', False),
                "is_bestseller": item.get('is_bestseller', False),
                "relevance_score": hit['_score']
            })
        
        logger.info(f"Generated {len(recommendations)} recommendations for {customer['personal_info']['name']}")
        return recommendations
    
    def redeem_points(self, customer_id: str, points_to_redeem: int, item_name: str) -> Tuple[bool, str, Dict]:
        """Redeem customer points for rewards"""
        customer = self.get_customer(customer_id)
        if not customer:
            return False, "Customer not found", {}
        
        current_points = customer['loyalty_profile']['total_points']
        
        if current_points < points_to_redeem:
            return False, f"Insufficient points. Current: {current_points}, Required: {points_to_redeem}", {}
        
        # Update customer points
        new_points = current_points - points_to_redeem
        customer['loyalty_profile']['total_points'] = new_points
        customer['loyalty_profile']['points_redeemed_ytd'] += points_to_redeem
        customer['loyalty_profile']['last_activity'] = datetime.now().isoformat()
        
        # Remove ML field to prevent duplicate token errors
        if 'ml' in customer:
            del customer['ml']
        
        success = self.es_client.update_document(Config.INDEX_CUSTOMERS, customer_id, customer)
        
        if success:
            logger.info(f"Successfully redeemed {points_to_redeem} points for {customer['personal_info']['name']}")
            return True, f"Successfully redeemed {points_to_redeem} points for {item_name}", {"new_balance": new_points}
        else:
            return False, "Failed to update customer points", {}
    
    # Points and Tier Calculation (unchanged)
    def calculate_points(self, order_total: float, channel: str, customer_tier: str) -> int:
        """Calculate points earned for an order"""
        base_points = 0
        
        if channel == "dine-in":
            base_points = int(order_total / 100) * 10
        elif channel in ["app", "delivery"]:
            base_points = int(order_total / 100) * 15
        
        multipliers = {"BeeBuddy": 1.0, "BeeFan": 1.2, "BeeElite": 1.5}
        return int(base_points * multipliers.get(customer_tier, 1.0))
    
    def check_tier_upgrade(self, annual_spending: float) -> str:
        """Check if customer qualifies for tier upgrade"""
        if annual_spending >= 5000:
            return "BeeElite"
        elif annual_spending >= 2000:
            return "BeeFan"
        else:
            return "BeeBuddy"
    
    # OPTIMIZED: Single Transaction Creation
    def create_transaction(self, customer_id: str, items: List[Dict], channel: str, 
                          store_info: Dict, payment_method: str = "cash") -> Tuple[bool, str, Dict]:
        """Create new transaction and update customer data - OPTIMIZED VERSION"""
        customer = self.get_customer(customer_id)
        if not customer:
            return False, "Customer not found", {}
        
        # Calculate order details
        order_total = sum(item['price'] * item['quantity'] for item in items)
        customer_tier = customer['loyalty_profile']['tier']
        points_earned = self.calculate_points(order_total, channel, customer_tier)
        
        # Create transaction record
        transaction_id = f"txn_{customer_id}_{str(uuid.uuid4())[:8]}"
        transaction_data = {
            "transaction_id": transaction_id,
            "customer_id": customer_id,
            "store_id": store_info.get('store_id', 'store_001'),
            "timestamp": datetime.now().isoformat(),
            "channel": channel,
            "location": store_info,
            "items": items,
            "order_total": order_total,
            "points_earned": points_earned,
            "points_redeemed": 0,
            "payment_method": payment_method,
            "order_type": channel,
            "hour_of_day": datetime.now().hour,
            "day_of_week": datetime.now().strftime("%A"),
            "is_weekend": datetime.now().weekday() >= 5
        }
        
        # Update customer data
        current_annual = customer['loyalty_profile']['annual_spending']
        new_annual = current_annual + order_total
        new_tier = self.check_tier_upgrade(new_annual)
        tier_upgraded = new_tier != customer_tier
        
        customer['loyalty_profile']['total_points'] += points_earned
        customer['loyalty_profile']['points_earned_ytd'] += points_earned
        customer['loyalty_profile']['annual_spending'] = new_annual
        customer['loyalty_profile']['tier'] = new_tier
        customer['loyalty_profile']['last_activity'] = datetime.now().isoformat()
        customer['purchase_behavior']['total_orders'] += 1
        
        # Remove ML field to prevent duplicate token errors
        if 'ml' in customer:
            del customer['ml']
        
        # OPTIMIZATION: Batch all updates together
        updates_successful = self._batch_transaction_updates(
            transaction_id, transaction_data,
            customer_id, customer,
            store_info.get('store_id', 'store_001'), items
        )
        
        if not updates_successful:
            return False, "Failed to process transaction", {}
        
        logger.info(f"Created transaction {transaction_id} for {customer['personal_info']['name']} - ₱{order_total}")
        
        return True, f"Transaction successful! Earned {points_earned} BeePoints.", {
            "transaction_id": transaction_id,
            "order_total": order_total,
            "points_earned": points_earned,
            "tier_upgraded": tier_upgraded,
            "new_tier": new_tier if tier_upgraded else customer_tier,
            "inventory_updated": True
        }
    
    def _batch_transaction_updates(self, transaction_id: str, transaction_data: Dict,
                                  customer_id: str, customer_data: Dict,
                                  store_id: str, items: List[Dict]) -> bool:
        """Batch all transaction-related updates for better performance"""
        try:
            # Prepare bulk update data
            bulk_updates = []
            
            # 1. Transaction document
            bulk_updates.extend([
                {"index": {"_index": Config.INDEX_TRANSACTIONS, "_id": transaction_id}},
                transaction_data
            ])
            
            # 2. Customer document
            bulk_updates.extend([
                {"index": {"_index": Config.INDEX_CUSTOMERS, "_id": customer_id}},
                customer_data
            ])
            
            # 3. Inventory updates
            inventory_updates = self._prepare_inventory_updates(store_id, items)
            bulk_updates.extend(inventory_updates)
            
            # Execute bulk update
            if bulk_updates:
                success = self._execute_bulk_update(bulk_updates)
                if success:
                    # Only refresh indices once at the end
                    self.es_client.refresh_index([Config.INDEX_TRANSACTIONS, Config.INDEX_CUSTOMERS, Config.INDEX_INVENTORY])
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Batch transaction updates failed: {str(e)}")
            return False
    
    def _prepare_inventory_updates(self, store_id: str, items: List[Dict]) -> List[Dict]:
        """Prepare inventory updates for bulk operation"""
        bulk_updates = []
        
        try:
            for item in items:
                # Find matching inventory item
                search_query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"store_id": store_id}},
                                {"match": {"item_name": item["name"]}}
                            ]
                        }
                    },
                    "size": 1
                }
                
                results = self.es_client.aggregation_search(Config.INDEX_INVENTORY, search_query)
                
                if results and results.get('hits', {}).get('hits'):
                    inventory_hit = results['hits']['hits'][0]
                    inventory_item = inventory_hit['_source']
                    inventory_id = inventory_hit['_id']
                    
                    # Update inventory data
                    new_stock = max(0, inventory_item['current_stock'] - item['quantity'])
                    inventory_item['current_stock'] = new_stock
                    inventory_item['timestamp'] = datetime.now().isoformat()
                    
                    # Update status based on new stock level
                    reorder_point = inventory_item['reorder_point']
                    if new_stock <= reorder_point * 0.5:
                        inventory_item['status'] = "Critical"
                    elif new_stock <= reorder_point:
                        inventory_item['status'] = "Low"
                    elif new_stock <= reorder_point * 2:
                        inventory_item['status'] = "Adequate"
                    else:
                        inventory_item['status'] = "Good"
                    
                    # Update predicted stockout
                    daily_consumption = inventory_item.get('daily_consumption', 10)
                    if daily_consumption > 0:
                        days_until_stockout = max(0, (new_stock - reorder_point) / daily_consumption)
                        predicted_stockout = datetime.now() + timedelta(days=days_until_stockout)
                        inventory_item['predicted_stockout_date'] = predicted_stockout.isoformat()
                    
                    # Add to bulk updates
                    bulk_updates.extend([
                        {"index": {"_index": Config.INDEX_INVENTORY, "_id": inventory_id}},
                        inventory_item
                    ])
            
            return bulk_updates
            
        except Exception as e:
            logger.error(f"Error preparing inventory updates: {str(e)}")
            return []
    
    def _execute_bulk_update(self, bulk_updates: List[Dict]) -> bool:
        """Execute bulk update using Elasticsearch bulk API"""
        try:
            # Convert to newline-delimited JSON format
            import json
            bulk_body = "\n".join(json.dumps(item) for item in bulk_updates) + "\n"
            
            # Send bulk request
            import requests
            response = requests.post(
                f"{self.es_client.endpoint}/_bulk",
                headers={**self.es_client.headers, "Content-Type": "application/x-ndjson"},
                data=bulk_body,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                errors = [item for item in result.get('items', []) if 'error' in item.get('index', {})]
                
                if errors:
                    logger.warning(f"{len(errors)} documents had errors during bulk update")
                    return len(errors) < len(bulk_updates) * 0.1  # Accept if < 10% errors
                else:
                    logger.info(f"Successfully bulk updated {len(bulk_updates)//2} documents")
                    return True
            else:
                logger.error(f"Bulk update failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Bulk update execution failed: {str(e)}")
            return False
    
    # OPTIMIZED: Bulk Transaction Creation
    def create_bulk_transactions(self, transaction_requests: List[Dict]) -> Dict:
        """Create multiple transactions efficiently using bulk operations"""
        if not transaction_requests:
            return {"success": False, "error": "No transactions to process"}
        
        start_time = datetime.now()
        
        # Prepare all transaction data
        all_transactions = []
        all_customers = {}
        all_inventory_updates = []
        total_revenue = 0
        
        logger.info(f"Processing {len(transaction_requests)} bulk transactions...")
        
        try:
            # Fetch all customers in batch
            customer_ids = list(set([req['customer_id'] for req in transaction_requests]))
            customers_data = self._fetch_customers_batch(customer_ids)
            
            # Process each transaction request
            for req in transaction_requests:
                customer_id = req['customer_id']
                items = req['items']
                channel = req['channel']
                store_info = req['store_info']
                payment_method = req.get('payment_method', 'cash')
                
                customer = customers_data.get(customer_id)
                if not customer:
                    continue
                
                # Calculate order details
                order_total = sum(item['price'] * item['quantity'] for item in items)
                customer_tier = customer['loyalty_profile']['tier']
                points_earned = self.calculate_points(order_total, channel, customer_tier)
                
                # Create transaction record
                transaction_id = f"txn_{customer_id}_{str(uuid.uuid4())[:8]}"
                transaction_data = {
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "store_id": store_info.get('store_id', 'store_001'),
                    "timestamp": datetime.now().isoformat(),
                    "channel": channel,
                    "location": store_info,
                    "items": items,
                    "order_total": order_total,
                    "points_earned": points_earned,
                    "points_redeemed": 0,
                    "payment_method": payment_method,
                    "order_type": channel,
                    "hour_of_day": datetime.now().hour,
                    "day_of_week": datetime.now().strftime("%A"),
                    "is_weekend": datetime.now().weekday() >= 5
                }
                
                all_transactions.append((transaction_id, transaction_data))
                total_revenue += order_total
                
                # Update customer data
                current_annual = customer['loyalty_profile']['annual_spending']
                new_annual = current_annual + order_total
                new_tier = self.check_tier_upgrade(new_annual)
                
                customer['loyalty_profile']['total_points'] += points_earned
                customer['loyalty_profile']['points_earned_ytd'] += points_earned
                customer['loyalty_profile']['annual_spending'] = new_annual
                customer['loyalty_profile']['tier'] = new_tier
                customer['loyalty_profile']['last_activity'] = datetime.now().isoformat()
                customer['purchase_behavior']['total_orders'] += 1
                
                # Remove ML field
                if 'ml' in customer:
                    del customer['ml']
                
                all_customers[customer_id] = customer
                
                # Prepare inventory updates
                inventory_updates = self._prepare_inventory_updates(store_info.get('store_id', 'store_001'), items)
                all_inventory_updates.extend(inventory_updates)
            
            # Execute all updates in one bulk operation
            bulk_updates = []
            
            # Add transactions
            for transaction_id, transaction_data in all_transactions:
                bulk_updates.extend([
                    {"index": {"_index": Config.INDEX_TRANSACTIONS, "_id": transaction_id}},
                    transaction_data
                ])
            
            # Add customers
            for customer_id, customer_data in all_customers.items():
                bulk_updates.extend([
                    {"index": {"_index": Config.INDEX_CUSTOMERS, "_id": customer_id}},
                    customer_data
                ])
            
            # Add inventory updates
            bulk_updates.extend(all_inventory_updates)
            
            # Execute bulk update
            success = self._execute_bulk_update(bulk_updates)
            
            if success:
                # Refresh indices once at the end
                self.es_client.refresh_index([Config.INDEX_TRANSACTIONS, Config.INDEX_CUSTOMERS, Config.INDEX_INVENTORY])
                
                processing_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Bulk processed {len(all_transactions)} transactions in {processing_time:.2f}s (₱{total_revenue})")
                
                return {
                    "success": True,
                    "transactions_created": len(all_transactions),
                    "total_revenue": total_revenue,
                    "processing_time_seconds": processing_time,
                    "performance_note": f"Processed {len(all_transactions)} orders in {processing_time:.2f}s"
                }
            else:
                return {"success": False, "error": "Bulk update failed"}
                
        except Exception as e:
            logger.error(f"Bulk transaction creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _fetch_customers_batch(self, customer_ids: List[str]) -> Dict:
        """Fetch multiple customers in a single query"""
        try:
            query = {
                "query": {"terms": {"_id": customer_ids}},
                "size": len(customer_ids)
            }
            
            response = self.es_client.aggregation_search(Config.INDEX_CUSTOMERS, query)
            
            customers = {}
            if response and response.get('hits', {}).get('hits'):
                for hit in response['hits']['hits']:
                    customers[hit['_id']] = hit['_source']
            
            return customers
            
        except Exception as e:
            logger.error(f"Error fetching customers batch: {str(e)}")
            return {}
    
    # Menu Search (unchanged)
    def search_menu(self, query_text: str, limit: int = 10) -> List[Dict]:
        """Semantic search through menu items"""
        results = self.es_client.semantic_search(
            Config.INDEX_MENU,
            query_text,
            size=limit,
            source_fields=["name", "category", "price", "description", "nutritional_info", 
                          "is_new", "is_bestseller", "points_value"]
        )
        
        menu_items = []
        for hit in results.get('hits', {}).get('hits', []):
            item = hit['_source']
            menu_items.append({
                "name": item['name'],
                "category": item['category'],
                "price": item['price'],
                "description": item['description'],
                "nutritional_info": item.get('nutritional_info', {}),
                "is_new": item.get('is_new', False),
                "is_bestseller": item.get('is_bestseller', False),
                "points_value": item.get('points_value', 0),
                "relevance_score": hit['_score']
            })
        
        logger.info(f"Menu search for '{query_text}' returned {len(menu_items)} results")
        return menu_items
    
    # Analytics (unchanged for now, but could be optimized further)
    def get_store_analytics(self) -> Dict:
        """Get real-time store performance analytics"""
        # Get all stores
        stores_query = {"query": {"match_all": {}}, "size": 20}
        stores_response = self.es_client.aggregation_search(Config.INDEX_STORES, stores_query)
        
        if not stores_response or not stores_response.get('hits', {}).get('hits'):
            return {"success": False, "error": "No stores found"}
        
        stores = [hit['_source'] for hit in stores_response['hits']['hits']]
        
        # Get recent transaction aggregations (last 24 hours)
        last_24h = (datetime.now() - timedelta(hours=24)).isoformat()
        
        agg_query = {
            "query": {"range": {"timestamp": {"gte": last_24h}}},
            "size": 0,
            "aggs": {
                "stores": {
                    "terms": {"field": "store_id", "size": 20},
                    "aggs": {
                        "total_revenue": {"sum": {"field": "order_total"}},
                        "order_count": {"value_count": {"field": "transaction_id"}},
                        "avg_order": {"avg": {"field": "order_total"}},
                        "channel_breakdown": {"terms": {"field": "channel"}}
                    }
                }
            }
        }
        
        agg_response = self.es_client.aggregation_search(Config.INDEX_TRANSACTIONS, agg_query)
        
        # Process results
        store_performance = {}
        if agg_response and agg_response.get('aggregations'):
            for bucket in agg_response['aggregations']['stores']['buckets']:
                store_id = bucket['key']
                store_performance[store_id] = {
                    "recent_orders": bucket['order_count']['value'],
                    "recent_revenue": bucket['total_revenue']['value'],
                    "avg_order_value": bucket['avg_order']['value'] if bucket['avg_order']['value'] else 0,
                    "channels": {ch['key']: ch['doc_count'] for ch in bucket['channel_breakdown']['buckets']}
                }
        
        # Combine store data with performance metrics
        enhanced_stores = []
        for store in stores:
            store_id = store['store_id']
            performance = store_performance.get(store_id, {
                "recent_orders": 0,
                "recent_revenue": 0,
                "avg_order_value": 0,
                "channels": {}
            })
            enhanced_stores.append({**store, **performance})
        
        logger.info(f"Retrieved analytics for {len(enhanced_stores)} stores")
        return {
            "success": True,
            "stores": enhanced_stores,
            "total_stores": len(enhanced_stores),
            "last_updated": datetime.now().isoformat()
        }
    
    def get_inventory_analytics(self, store_id: str) -> Dict:
        """FIXED: Get real-time inventory analytics for a store"""
        # FIXED: Updated query to properly search for inventory items
        inventory_query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"store_id": store_id}}
                    ]
                }
            },
            "size": 100,
            "sort": [
                {"timestamp": {"order": "desc"}}, 
                {"status": {"order": "desc"}}, 
                {"current_stock": {"order": "asc"}}
            ]
        }
        
        response = self.es_client.aggregation_search(Config.INDEX_INVENTORY, inventory_query)
        
        if not response or not response.get('hits', {}).get('hits'):
            logger.warning(f"No inventory data found for store {store_id}")
            
            # Try to get inventory from any store to debug
            debug_query = {"query": {"match_all": {}}, "size": 10}
            debug_response = self.es_client.aggregation_search(Config.INDEX_INVENTORY, debug_query)
            
            if debug_response and debug_response.get('hits', {}).get('hits'):
                logger.info(f"Found {len(debug_response['hits']['hits'])} total inventory items in system")
                sample_stores = set()
                for hit in debug_response['hits']['hits']:
                    sample_stores.add(hit['_source'].get('store_id', 'unknown'))
                logger.info(f"Sample store IDs in inventory: {list(sample_stores)}")
            
            return {"success": False, "error": f"No inventory data found for store {store_id}"}
        
        items = [hit['_source'] for hit in response['hits']['hits']]
        
        # Calculate insights
        total_items = len(items)
        critical_items = [item for item in items if item['status'] == 'Critical']
        low_items = [item for item in items if item['status'] == 'Low']
        
        # Generate recommendations
        recommendations = []
        for item in critical_items + low_items:
            urgency = "CRITICAL: Immediate reorder required!" if item['status'] == 'Critical' else "WARNING: Schedule reorder soon"
            recommendations.append({
                "item": item['item_name'],
                "action": urgency,
                "current_stock": item['current_stock'],
                "reorder_point": item['reorder_point'],
                "predicted_stockout": item.get('predicted_stockout_date', ''),
                "priority": "high" if item['status'] == 'Critical' else "medium"
            })
        
        logger.info(f"Retrieved inventory analytics for store {store_id}: {total_items} items, {len(critical_items)} critical")
        
        return {
            "success": True,
            "store_id": store_id,
            "inventory_summary": {
                "total_items": total_items,
                "critical_items": len(critical_items),
                "low_items": len(low_items),
                "adequate_items": len([item for item in items if item['status'] in ['Adequate', 'Good']])
            },
            "inventory_items": items,
            "recommendations": recommendations,
            "last_updated": datetime.now().isoformat()
        }
