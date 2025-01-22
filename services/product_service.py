# services/product_service.py
from bson import ObjectId

class ProductService:
    def __init__(self, db):
        self.db = db

    def create_product(self, product_data):
        """Create a new product"""
        # Validate required fields
        required_fields = ['name', 'description', 'category', 'price', 'sku']
        for field in required_fields:
            if field not in product_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate SKU uniqueness
        if self.db.products.find_one({"sku": product_data["sku"]}):
            raise ValueError("SKU already exists")

        # Insert the product
        result = self.db.products.insert_one(product_data)
        return {
            "message": "Product created successfully",
            "id": str(result.inserted_id)
        }

    def get_product_by_id(self, product_id):
        """Get a product by ID"""
        try:
            product = self.db.products.find_one({"_id": ObjectId(product_id)})
            if not product:
                raise ValueError("Product not found")
            product["id"] = str(product.pop("_id"))
            return product
        except ValueError as e:
            raise e  # Re-raise ValueError without additional message
        except Exception as e:
            raise ValueError(f"Invalid product ID: {str(e)}")

    def update_product(self, product_id, update_data):
        """Update a product"""
        try:
            # Check if product exists
            if not self.db.products.find_one({"_id": ObjectId(product_id)}):
                raise ValueError("Product not found")

            # If SKU is being updated, check for uniqueness
            if "sku" in update_data:
                existing = self.db.products.find_one({
                    "sku": update_data["sku"],
                    "_id": {"$ne": ObjectId(product_id)}
                })
                if existing:
                    raise ValueError("SKU already exists")

            # Update the product
            result = self.db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data}
            )

            if result.modified_count:
                return {"message": "Product updated successfully"}
            return {"message": "No changes made to product"}

        except ValueError as e:
            raise e  # Re-raise ValueError without additional message
        except Exception as e:
            raise ValueError(f"Invalid product ID: {str(e)}")

    def delete_product(self, product_id):
        """Delete a product"""
        try:
            # Check if product exists
            if not self.db.products.find_one({"_id": ObjectId(product_id)}):
                raise ValueError("Product not found")

            # Check if product is referenced in inventory
            if self.db.inventory.find_one({"productId": ObjectId(product_id)}):
                raise ValueError("Cannot delete product that exists in inventory")

            # Delete the product
            result = self.db.products.delete_one({"_id": ObjectId(product_id)})
            
            if result.deleted_count:
                return {"message": "Product deleted successfully"}
            return {"message": "Product not found"}

        except ValueError as e:
            raise e  # Re-raise ValueError without additional message
        except Exception as e:
            raise ValueError(f"Invalid product ID: {str(e)}")

    def get_all_products(self, skip=0, limit=50):
        """Get all products with pagination"""
        products = list(self.db.products.find().skip(skip).limit(limit))
        for product in products:
            product["id"] = str(product.pop("_id"))
        return products

    def search_products(self, query):
        """Search products by name, description, or SKU"""
        filter_query = {
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"sku": {"$regex": query, "$options": "i"}}
            ]
        }
        products = list(self.db.products.find(filter_query))
        for product in products:
            product["id"] = str(product.pop("_id"))
        return products
