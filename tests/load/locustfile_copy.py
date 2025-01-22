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
        logger.info("User session initialized with test data")

    # Product Management Tasks
    @task(3)
    def get_products(self):
        """List all products (GET /products)"""
        with self.client.get("/products", name="List Products") as response:
            if response.status_code == 200:
                products = response.json()
                if products and isinstance(products, list):
                    self.created_product_ids = [p['id'] for p in products]
                    logger.debug(f"Retrieved {len(products)} products")
            else:
                logger.warning(f"Get products failed with status {response.status_code}")

    @task(2)
    def get_single_product(self):
        """Get a single product by ID (GET /products/{id})"""
        if self.created_product_ids:
            product_id = choice(self.created_product_ids)
            with self.client.get(
                f"/products/{product_id}",
                name="Get Single Product"
            ) as response:
                logger.debug(f"Get product {product_id}: status {response.status_code}")

    @task(1)
    def create_product(self):
        """Create a new product (POST /products)"""
        product_data = choice(self.test_products).copy()
        product_data["sku"] = f"{product_data['sku']}{randint(1000, 9999)}"
        
        with self.client.post(
            "/products",
            json=product_data,
            name="Create Product"
        ) as response:
            if response.status_code == 201:
                product_id = response.json().get('id')
                if product_id:
                    self.created_product_ids.append(product_id)
                    logger.debug(f"Created product {product_id}")
            else:
                logger.warning(f"Create product failed with status {response.status_code}")

    @task(1)
    def update_product(self):
        """Update an existing product (PUT /products/{id})"""
        if self.created_product_ids:
            product_id = choice(self.created_product_ids)
            update_data = {
                "price": round(randint(1000, 5000) / 100, 2),
                "description": f"Updated description {randint(1, 1000)}"
            }
            with self.client.put(
                f"/products/{product_id}",
                json=update_data,
                name="Update Product"
            ) as response:
                logger.debug(f"Update product {product_id}: status {response.status_code}")

    @task(1)
    def delete_product(self):
        """Delete a product (DELETE /products/{id})"""
        if self.created_product_ids:
            product_id = choice(self.created_product_ids)
            with self.client.delete(
                f"/products/{product_id}",
                name="Delete Product"
            ) as response:
                if response.status_code == 200:
                    self.created_product_ids.remove(product_id)
                    logger.debug(f"Deleted product {product_id}")

    # Inventory Management Tasks
    @task(2)
    def create_inventory(self):
        """Create inventory entry (POST /inventory)"""
        if self.created_product_ids:
            inventory_data = {
                "productId": choice(self.created_product_ids),
                "storeId": choice(self.store_ids),
                "quantity": randint(50, 200),
                "minStock": randint(10, 30)
            }
            with self.client.post(
                "/inventory",
                json=inventory_data,
                name="Create Inventory"
            ) as response:
                logger.debug(f"Create inventory: status {response.status_code}")

    @task(2)
    def get_store_inventory(self):
        """Get store inventory (GET /stores/{id}/inventory)"""
        store_id = choice(self.store_ids)
        with self.client.get(
            f"/stores/{store_id}/inventory",
            name="Get Store Inventory"
        ) as response:
            logger.debug(f"Get store {store_id} inventory: status {response.status_code}")

    @task(1)
    def transfer_stock(self):
        """Transfer stock between stores (POST /inventory/transfer)"""
        if self.created_product_ids:
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
                name="Transfer Stock"
            ) as response:
                logger.debug(f"Transfer stock: status {response.status_code}")

    @task(1)
    def check_stock_alerts(self):
        """Check low stock alerts (GET /inventory/alert)"""
        with self.client.get(
            "/inventory/alert",
            name="Check Stock Alerts"
        ) as response:
            logger.debug(f"Check stock alerts: status {response.status_code}")
