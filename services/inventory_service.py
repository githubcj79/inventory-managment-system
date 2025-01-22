# services/inventory_service.py
from bson import ObjectId

class InventoryService:
    def __init__(self, db):
        self.db = db

    def get_product_stock(self, product_id):
        """Get current stock for a product"""
        try:
            # Validate product exists
            if not self.db.products.find_one({"_id": ObjectId(product_id)}):
                raise ValueError("Product not found")

            # Get inventory
            inventory = self.db.inventory.find_one({"productId": ObjectId(product_id)})
            return {
                "productId": str(product_id),
                "quantity": inventory["quantity"] if inventory else 0
            }
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error retrieving stock: {str(e)}")

    def get_all_stock(self):
        """Get current stock for all products"""
        try:
            inventory = list(self.db.inventory.find())
            return [{
                "productId": str(item["productId"]),
                "quantity": item["quantity"]
            } for item in inventory]
        except Exception as e:
            raise ValueError(f"Error retrieving inventory: {str(e)}")

    def get_low_stock_products(self, threshold=10):
        """Get products with stock below threshold"""
        try:
            low_stock = list(self.db.inventory.find({"quantity": {"$lte": threshold}}))
            return [{
                "productId": str(item["productId"]),
                "quantity": item["quantity"]
            } for item in low_stock]
        except Exception as e:
            raise ValueError(f"Error retrieving low stock products: {str(e)}")

    def adjust_stock(self, product_id, quantity):
        """Manually adjust stock quantity"""
        try:
            # Validate product exists
            if not self.db.products.find_one({"_id": ObjectId(product_id)}):
                raise ValueError("Product not found")

            # Validate quantity
            if not isinstance(quantity, (int, float)) or quantity < 0:
                raise ValueError("Quantity must be a positive number")

            # Update inventory
            result = self.db.inventory.update_one(
                {"productId": ObjectId(product_id)},
                {
                    "$set": {"quantity": quantity},
                    "$setOnInsert": {"productId": ObjectId(product_id)}
                },
                upsert=True
            )

            return {"message": "Stock adjusted successfully"}
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error adjusting stock: {str(e)}")

    def adjust_multiple_stocks(self, adjustments):
        """
        Adjust stock for multiple products at once
        adjustments: list of tuples (product_id, quantity)
        """
        try:
            # Validate all products and quantities first
            for product_id, quantity in adjustments:
                if not self.db.products.find_one({"_id": ObjectId(product_id)}):
                    raise ValueError(f"Product {product_id} not found")
                if not isinstance(quantity, (int, float)) or quantity < 0:
                    raise ValueError(f"Invalid quantity for product {product_id}")

            operations = [
                {
                    "updateOne": {
                        "filter": {"productId": ObjectId(pid)},
                        "update": {
                            "$set": {"quantity": qty},
                            "$setOnInsert": {"productId": ObjectId(pid)}
                        },
                        "upsert": True
                    }
                }
                for pid, qty in adjustments
            ]
            
            result = self.db.inventory.bulk_write(operations)
            return {
                "message": "Stocks adjusted successfully",
                "modified_count": result.modified_count,
                "upserted_count": result.upserted_count
            }
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error adjusting stocks: {str(e)}")

    def validate_stock_level(self, product_id, min_threshold=10, max_threshold=1000):
        """Validate if stock is within acceptable thresholds"""
        try:
            # First check if product exists and get current stock
            inventory = self.get_product_stock(product_id)
            quantity = inventory["quantity"]
            
            return {
                "productId": str(product_id),
                "quantity": quantity,
                "status": "low" if quantity < min_threshold else 
                         "excess" if quantity > max_threshold else 
                         "normal",
                "thresholds": {
                    "min": min_threshold,
                    "max": max_threshold
                }
            }
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error validating stock: {str(e)}")
