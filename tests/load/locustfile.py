from locust import HttpUser, task, between
from bson import ObjectId
import json
import random

class InventorySystemUser(HttpUser):
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def on_start(self):
        """Initialize test data"""
        # Create a product first
        self.product_data = {
            "name": f"Test Product {ObjectId()}",
            "description": "Load test product",
            "category": "test_category",
            "price": 99.99,
            "sku": f"TST{ObjectId()}"
        }
        
        # Create product
        response = self.client.post(
            "/products",  # Removed /api prefix
            json=self.product_data,
            headers=self.headers
        )
        
        if response.status_code in [200, 201]:
            response_data = response.json()
            self.product_id = response_data.get("id")
            print(f"Successfully created product with ID: {self.product_id}")
            
            # Initialize inventory for store001
            self.inventory_data = {
                "productId": self.product_id,
                "storeId": "store001",
                "quantity": 1000,
                "minStock": 100
            }
            inv_response = self.client.post(
                "/inventory",  # Removed /api prefix
                json=self.inventory_data,
                headers=self.headers
            )
            if inv_response.status_code in [200, 201]:
                print(f"Successfully initialized inventory for product {self.product_id}")
            else:
                print(f"Failed to initialize inventory (Status {inv_response.status_code}): {inv_response.text}")
        else:
            print(f"Failed to create product (Status {response.status_code}): {response.text}")

    @task(3)
    def list_products(self):
        """Test getting product list"""
        with self.client.get(
            "/products",  # Removed /api prefix
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get products list: {response.text}")

    @task(2)
    def get_product(self):
        """Test getting single product"""
        if hasattr(self, 'product_id'):
            with self.client.get(
                f"/products/{self.product_id}",  # Removed /api prefix
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to get product: {response.text}")

    @task(2)
    def update_product(self):
        """Test updating product"""
        if hasattr(self, 'product_id'):
            update_data = {
                "price": random.uniform(50, 150)
            }
            with self.client.put(
                f"/products/{self.product_id}",  # Removed /api prefix
                json=update_data,
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to update product: {response.text}")

    @task(3)
    def get_store_inventory(self):
        """Test getting store inventory"""
        with self.client.get(
            "/stores/store001/inventory",  # Removed /api prefix
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get store inventory: {response.text}")

    @task(2)
    def transfer_stock(self):
        """Test stock transfer between stores"""
        if hasattr(self, 'product_id'):
            transfer_data = {
                "productId": self.product_id,
                "sourceStoreId": "store001",
                "targetStoreId": "store002",
                "quantity": random.randint(1, 10)
            }
            with self.client.post(
                "/inventory/transfer",  # Removed /api prefix
                json=transfer_data,
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Failed to transfer stock: {response.text}")

    @task(1)
    def check_low_stock_alerts(self):
        """Test getting low stock alerts"""
        with self.client.get(
            "/inventory/alert",  # Removed /api prefix
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get low stock alerts: {response.text}")

    @task(1)
    def create_inventory(self):
        """Test creating new inventory entry"""
        if hasattr(self, 'product_id'):
            inventory_data = {
                "productId": self.product_id,
                "storeId": f"store{random.randint(3, 10)}",
                "quantity": random.randint(100, 1000),
                "minStock": 50
            }
            with self.client.post(
                "/inventory",  # Removed /api prefix
                json=inventory_data,
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code in [200, 201]:
                    response.success()
                else:
                    response.failure(f"Failed to create inventory: {response.text}")

    def on_stop(self):
        """Cleanup after tests"""
        if hasattr(self, 'product_id'):
            try:
                response = self.client.delete(
                    f"/products/{self.product_id}",  # Removed /api prefix
                    headers=self.headers
                )
                if response.status_code in [200, 204]:
                    print(f"Successfully cleaned up product {self.product_id}")
                else:
                    print(f"Failed to clean up product {self.product_id} (Status {response.status_code})")
            except Exception as e:
                print(f"Cleanup failed for product {self.product_id}: {e}")
