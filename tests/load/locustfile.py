"""
Locust load testing script for Inventory Management System API.
Tests all endpoints defined in the SAM template.
"""

from locust import HttpUser, task, between
from random import randint, choice
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InventoryManagementUser(HttpUser):
    """
    Simulates user behavior for load testing the Inventory Management System API.
    Includes all endpoints defined in the SAM template.
    """
    
    # Wait 1-5 seconds between tasks
    wait_time = between(1, 5)
    
    def on_start(self):
        """
        Initialize test data and state when user starts.
        Sets up sample products and store IDs.
        """
        # Sample product data for creation
        self.test_products = [
            {
                "name": "Steel Bar Type A",
                "description": "High-quality steel bar for construction",
                "category": "raw_materials",
                "price": 29.99,
                "sku": f"STL{randint(1000, 9999)}"
            },
            {
                "name": "Iron Rod Type B",
                "description": "Standard iron rod for industrial use",
                "category": "raw_materials",
                "price": 19.99,
                "sku": f"IRN{randint(1000, 9999)}"
            },
            {
                "name": "Copper Wire Type C",
                "description": "Premium copper wire for electrical use",
                "category": "raw_materials",
                "price": 39.99,
                "sku": f"CPR{randint(1000, 9999)}"
            }
        ]
        # Track created products for other operations
        self.created_product_ids = []
        # Sample store IDs for inventory operations
        self.store_ids = ["store001", "store002", "store003"]
        # Initialize by getting existing products
        self.get_products()
        logger.info("User session initialized with test data")

    # Product Management Tasks
    @task(3)
    def get_products(self):
        """List all products"""
        with self.client.get("/products", catch_response=True) as response:
            if response.status_code == 200:
                products = response.json()
                if products and isinstance(products, list):
                    self.created_product_ids = [p['id'] for p in products]
                    logger.debug(f"Retrieved {len(products)} products")
                response.success()
            else:
                response.failure(f"Get products failed with status {response.status_code}")

    @task(2)
    def get_single_product(self):
        """Get a single product by ID"""
        if not self.created_product_ids:
            return

        product_id = choice(self.created_product_ids)
        with self.client.get(
            f"/products/{product_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Remove non-existent product ID from our list
                self.created_product_ids.remove(product_id)
                response.failure(f"Product {product_id} not found")
            else:
                response.failure(f"Get product failed with status {response.status_code}")

    @task(1)
    def create_product(self):
        """Create a new product"""
        product_data = choice(self.test_products).copy()
        product_data["sku"] = f"{product_data['sku']}{randint(1000, 9999)}"
        
        with self.client.post(
            "/products",
            json=product_data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                try:
                    result = response.json()
                    if 'id' in result:
                        self.created_product_ids.append(result['id'])
                        response.success()
                    else:
                        response.failure("No product ID in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Create product failed with status {response.status_code}")

    @task(1)
    def update_product(self):
        """Update an existing product"""
        if not self.created_product_ids:
            return

        product_id = choice(self.created_product_ids)
        update_data = {
            "price": round(randint(1000, 5000) / 100, 2),
            "description": f"Updated description {randint(1, 1000)}"
        }
        
        with self.client.put(
            f"/products/{product_id}",
            json=update_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                self.created_product_ids.remove(product_id)
                response.failure(f"Product {product_id} not found")
            else:
                response.failure(f"Update product failed with status {response.status_code}")

    @task(1)
    def delete_product(self):
        """Delete a product"""
        if not self.created_product_ids:
            return

        product_id = choice(self.created_product_ids)
        with self.client.delete(
            f"/products/{product_id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                self.created_product_ids.remove(product_id)
                response.success()
            elif response.status_code == 404:
                self.created_product_ids.remove(product_id)
                response.failure(f"Product {product_id} not found")
            else:
                response.failure(f"Delete product failed with status {response.status_code}")

    # Inventory Management Tasks
    @task(2)
    def create_inventory(self):
        """Create inventory entry"""
        if not self.created_product_ids:
            return

        inventory_data = {
            "productId": choice(self.created_product_ids),
            "storeId": choice(self.store_ids),
            "quantity": randint(50, 200),
            "minStock": randint(10, 30)
        }
        
        with self.client.post(
            "/inventory",
            json=inventory_data,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Create inventory failed with status {response.status_code}")

    @task(2)
    def get_store_inventory(self):
        """Get store inventory"""
        store_id = choice(self.store_ids)
        with self.client.get(
            f"/stores/{store_id}/inventory",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Get store inventory failed with status {response.status_code}")

    @task(1)
    def transfer_stock(self):
        """Transfer stock between stores"""
        if not self.created_product_ids:
            return

        source_store = choice(self.store_ids)
        target_store = choice([s for s in self.store_ids if s != source_store])
        transfer_data = {
            "productId": choice(self.created_product_ids),
            "sourceStoreId": source_store,
            "targetStoreId": target_store,
            "quantity": randint(5, 20)
        }
        
        with self.client.post(
            "/inventory/transfer",
            json=transfer_data,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Transfer stock failed with status {response.status_code}")

    @task(1)
    def check_stock_alerts(self):
        """Check low stock alerts"""
        with self.client.get(
            "/inventory/alert",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Check stock alerts failed with status {response.status_code}")
