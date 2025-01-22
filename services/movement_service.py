# services/movement_service.py
from datetime import datetime
from bson import ObjectId

class MovementService:
    def __init__(self, db):
        self.db = db

    def create_movement(self, movement_data):
        """Create a new inventory movement"""
        try:
            # Validate required fields
            if "productId" not in movement_data:
                raise ValueError("productId is required")
            if "type" not in movement_data:
                raise ValueError("type is required")
            if "quantity" not in movement_data:
                raise ValueError("quantity is required")

            # Validate product exists
            try:
                product_id = ObjectId(movement_data["productId"])
                if not self.db.products.find_one({"_id": product_id}):
                    raise ValueError("Product not found")
            except ValueError as e:
                raise e  # Re-raise ValueError for "Product not found"
            except Exception:
                raise ValueError("Invalid product ID format")

            # Validate movement type
            if movement_data["type"] not in ["IN", "OUT"]:
                raise ValueError("Invalid movement type. Must be 'IN' or 'OUT'")

            # Validate quantity
            if movement_data["quantity"] <= 0:
                raise ValueError("Quantity must be positive")

            # Check stock for OUT movements
            if movement_data["type"] == "OUT":
                current_stock = self.db.inventory.find_one({"productId": product_id})
                current_quantity = current_stock["quantity"] if current_stock else 0
                if current_quantity < movement_data["quantity"]:
                    raise ValueError("Insufficient stock")

            # Convert productId to ObjectId
            movement_data["productId"] = product_id
            
            # Insert movement
            result = self.db.movements.insert_one(movement_data)

            # Update inventory
            update_quantity = movement_data["quantity"] if movement_data["type"] == "IN" else -movement_data["quantity"]
            self.db.inventory.update_one(
                {"productId": movement_data["productId"]},
                {
                    "$inc": {"quantity": update_quantity},
                    "$setOnInsert": {"productId": movement_data["productId"]}
                },
                upsert=True
            )

            return {
                "message": "Movement created successfully",
                "id": str(result.inserted_id)
            }

        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error creating movement: {str(e)}")

    def get_movement_by_id(self, movement_id):
        """Get a movement by ID"""
        try:
            try:
                movement = self.db.movements.find_one({"_id": ObjectId(movement_id)})
            except Exception:
                raise ValueError("Invalid movement ID format")

            if not movement:
                raise ValueError("Movement not found")
            
            return self._format_movement(movement)
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error retrieving movement: {str(e)}")

    def get_movements_by_product(self, product_id):
        """Get all movements for a specific product"""
        try:
            try:
                object_id = ObjectId(product_id)
            except Exception:
                raise ValueError("Invalid product ID format")

            movements = list(self.db.movements.find({"productId": object_id}))
            return [self._format_movement(movement) for movement in movements]
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error retrieving movements: {str(e)}")

    def get_movements_by_date_range(self, start_date, end_date):
        """Get movements within a date range"""
        try:
            movements = list(self.db.movements.find({
                "date": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }))
            return [self._format_movement(movement) for movement in movements]
        except Exception as e:
            raise ValueError(f"Error retrieving movements: {str(e)}")

    def get_movements_by_type(self, movement_type):
        """Get movements by type (IN/OUT)"""
        try:
            if movement_type not in ["IN", "OUT"]:
                raise ValueError("Invalid movement type. Must be 'IN' or 'OUT'")
            
            movements = list(self.db.movements.find({"type": movement_type}))
            return [self._format_movement(movement) for movement in movements]
        except ValueError as e:
            raise e
        except Exception as e:
            raise ValueError(f"Error retrieving movements: {str(e)}")

    def _format_movement(self, movement):
        """Helper method to format movement data"""
        try:
            if "_id" not in movement and "id" not in movement:
                raise ValueError("Movement must have an ID")

            formatted = movement.copy()
            if "_id" in formatted:
                formatted["id"] = str(formatted.pop("_id"))
            if "productId" in formatted:
                formatted["productId"] = str(formatted["productId"])
            return formatted
        except Exception as e:
            raise ValueError(f"Error formatting movement: {str(e)}")
