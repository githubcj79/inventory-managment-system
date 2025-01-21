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
