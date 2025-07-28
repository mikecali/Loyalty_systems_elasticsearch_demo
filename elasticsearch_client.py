"""
Fixed Elasticsearch client wrapper for Jollibee BeeLoyalty System
FIXED: Inventory ID priority issue in bulk indexing
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
from config import Config

# Configure logging
logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL), format=Config.LOG_FORMAT)
logger = logging.getLogger(__name__)

class ElasticsearchClient:
    """Enhanced Elasticsearch client with semantic search capabilities"""
    
    def __init__(self):
        """Initialize Elasticsearch client"""
        Config.validate()
        
        self.endpoint = Config.ELASTICSEARCH_ENDPOINT.rstrip('/')
        self.headers = {
            "Authorization": f"ApiKey {Config.ELASTICSEARCH_API_KEY}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"Initialized Elasticsearch client for {self.endpoint}")
    
    def request(self, method: str, path: str, data: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Make request to Elasticsearch
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            data: Request payload
            
        Returns:
            Response object or None if request failed
        """
        url = f"{self.endpoint}{path}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Log request details
            logger.debug(f"{method} {url} - Status: {response.status_code}")
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Elasticsearch request failed: {method} {url} - Error: {str(e)}")
            return None
    
    def health_check(self) -> Dict:
        """Check Elasticsearch cluster health"""
        response = self.request("GET", "/_cluster/health")
        
        if response and response.status_code == 200:
            health_data = response.json()
            logger.info(f"Cluster health: {health_data.get('status', 'unknown')}")
            return {
                "status": "healthy",
                "cluster_status": health_data.get('status', 'unknown'),
                "cluster_name": health_data.get('cluster_name', 'unknown'),
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error("Elasticsearch cluster health check failed")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat()
            }
    
    def create_index(self, index_name: str, mapping: Dict) -> bool:
        """Create index with mapping"""
        logger.info(f"Creating index: {index_name}")
        
        # Delete existing index if it exists
        delete_response = self.request("DELETE", f"/{index_name}")
        if delete_response:
            logger.info(f"Deleted existing index: {index_name}")
        
        # Create new index
        response = self.request("PUT", f"/{index_name}", mapping)
        
        if response and response.status_code in [200, 201]:
            logger.info(f"Successfully created index: {index_name}")
            return True
        else:
            logger.error(f"Failed to create index: {index_name}")
            if response:
                logger.error(f"Error response: {response.text}")
            return False
    
    def bulk_index(self, index_name: str, documents: List[Dict]) -> bool:
        """FIXED: Bulk index documents with proper ID priority"""
        logger.info(f"Bulk indexing {len(documents)} documents to {index_name}")
        
        # Prepare bulk data
        bulk_data = []
        for doc in documents:
            # FIXED: Determine document ID based on index type and available fields
            doc_id = self._determine_document_id(index_name, doc)
            
            if not doc_id:
                # Generate ID if none found
                import uuid
                doc_id = str(uuid.uuid4())
                logger.warning(f"No appropriate ID field found for document in {index_name}, generated: {doc_id}")
            
            bulk_data.append(json.dumps({"index": {"_index": index_name, "_id": doc_id}}))
            bulk_data.append(json.dumps(doc))
        
        # Convert to newline-delimited JSON
        bulk_body = "\n".join(bulk_data) + "\n"
        
        # Send bulk request
        response = requests.post(
            f"{self.endpoint}/_bulk",
            headers={**self.headers, "Content-Type": "application/x-ndjson"},
            data=bulk_body,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            errors = [item for item in result.get('items', []) if 'error' in item.get('index', {})]
            
            if errors:
                logger.warning(f"{len(errors)} documents had errors during bulk indexing")
                for error in errors[:3]:  # Log first 3 errors
                    logger.error(f"Bulk index error: {error['index']['error']}")
                return len(errors) < len(documents) * 0.1  # Return True if < 10% errors
            else:
                logger.info(f"Successfully bulk indexed all {len(documents)} documents")
                return True
        else:
            logger.error(f"Bulk indexing failed: {response.status_code}")
            logger.error(f"Error response: {response.text}")
            return False
    
    def _determine_document_id(self, index_name: str, doc: Dict) -> Optional[str]:
        """FIXED: Determine the appropriate document ID based on index type and available fields"""
        
        # Define ID priority for each index type
        id_priorities = {
            Config.INDEX_INVENTORY: ['inventory_id', 'id'],  # inventory_id first for inventory
            Config.INDEX_CUSTOMERS: ['customer_id', 'id'],
            Config.INDEX_TRANSACTIONS: ['transaction_id', 'id'],
            Config.INDEX_STORES: ['store_id', 'id'],
            Config.INDEX_MENU: ['item_id', 'id'],
        }
        
        # Get priority list for this index, or use default
        priority_fields = id_priorities.get(index_name, [
            'id', 'item_id', 'customer_id', 'transaction_id', 'inventory_id', 'store_id'
        ])
        
        # Try fields in priority order
        for field in priority_fields:
            if field in doc and doc[field]:
                logger.debug(f"Using {field} as document ID for {index_name}: {doc[field]}")
                return str(doc[field])
        
        # Fallback: try any field ending with '_id'
        for key, value in doc.items():
            if key.endswith('_id') and value:
                logger.debug(f"Using fallback ID field {key} for {index_name}: {value}")
                return str(value)
        
        return None
    
    def semantic_search(self, index_name: str, query_text: str, size: int = 10, 
                       source_fields: Optional[List[str]] = None) -> Dict:
        """
        Perform semantic search using ELSER
        
        Args:
            index_name: Index to search
            query_text: Search query text
            size: Number of results to return
            source_fields: Fields to return in results
            
        Returns:
            Search results dictionary
        """
        search_query = {
            "query": {
                "text_expansion": {
                    "ml.tokens": {
                        "model_id": Config.ELSER_MODEL_ID,
                        "model_text": query_text
                    }
                }
            },
            "size": size
        }
        
        if source_fields:
            search_query["_source"] = source_fields
        
        response = self.request("POST", f"/{index_name}/_search", search_query)
        
        if response and response.status_code == 200:
            results = response.json()
            logger.info(f"Semantic search returned {len(results.get('hits', {}).get('hits', []))} results")
            return results
        else:
            logger.error(f"Semantic search failed for query: {query_text}")
            return {"hits": {"hits": []}}
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        response = self.request("GET", f"/{index_name}/_doc/{doc_id}")
        
        if response and response.status_code == 200:
            return response.json()['_source']
        else:
            logger.warning(f"Document not found: {index_name}/{doc_id}")
            return None
    
    def update_document(self, index_name: str, doc_id: str, document: Dict) -> bool:
        """Update document"""
        response = self.request("PUT", f"/{index_name}/_doc/{doc_id}", document)
        
        if response and response.status_code in [200, 201]:
            logger.info(f"Successfully updated document: {index_name}/{doc_id}")
            return True
        else:
            logger.error(f"Failed to update document: {index_name}/{doc_id}")
            return False
    
    def aggregation_search(self, index_name: str, query: Dict) -> Dict:
        """Perform aggregation search"""
        response = self.request("POST", f"/{index_name}/_search", query)
        
        if response and response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Aggregation search failed on index: {index_name}")
            return {}
    
    def refresh_index(self, index_names: Union[str, List[str]]) -> bool:
        """Refresh index(es) for real-time search"""
        if isinstance(index_names, list):
            indices = ",".join(index_names)
        else:
            indices = index_names
        
        response = self.request("POST", f"/{indices}/_refresh")
        
        if response and response.status_code == 200:
            logger.info(f"Successfully refreshed indices: {indices}")
            return True
        else:
            logger.error(f"Failed to refresh indices: {indices}")
            return False
    
    # ADDITIONAL HELPER METHODS
    
    def count_documents(self, index_name: str, query: Optional[Dict] = None) -> int:
        """Count documents in index"""
        if query is None:
            query = {"query": {"match_all": {}}}
        
        response = self.request("POST", f"/{index_name}/_count", query)
        
        if response and response.status_code == 200:
            result = response.json()
            return result.get('count', 0)
        else:
            logger.error(f"Failed to count documents in {index_name}")
            return 0
    
    def delete_by_query(self, index_name: str, query: Dict) -> bool:
        """Delete documents matching query"""
        response = self.request("POST", f"/{index_name}/_delete_by_query", query)
        
        if response and response.status_code == 200:
            result = response.json()
            deleted = result.get('deleted', 0)
            logger.info(f"Deleted {deleted} documents from {index_name}")
            return True
        else:
            logger.error(f"Failed to delete documents from {index_name}")
            return False
