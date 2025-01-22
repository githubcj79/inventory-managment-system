"""
Inventory Management System API

This module implements a REST API for managing product inventory across multiple stores.
It provides functionality for product management, inventory tracking, stock transfers,
and low stock alerts.

Key Features:
    - Product CRUD operations with SKU validation
    - Inventory management with minimum stock levels
    - Stock transfer between stores
    - Movement tracking (IN, OUT, TRANSFER)
    - Low stock alerts
    - MongoDB integration for data persistence
"""

import json
import os
from datetime import datetime
from bson import ObjectId
from common.db_utils import get_mongo_client
from enum import Enum
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from decorators.logging_decorator import log_request

# Initialize logger and MongoDB connection
logger = Logger(service="inventory-management")
try:
    mongo_client = get_mongo_client()
    db = mongo_client["inventory_management"]
    logger.info("MongoDB connection initialized at module level")
except Exception as e:
    logger.error("Failed to initialize MongoDB connection at module level", extra={"error": str(e)})
    raise

class MovementType(Enum):
    """
    Enumeration of possible inventory movement types.
    
    Values:
        IN: Initial stock or restocking
        OUT: Stock removal or sales
        TRANSFER: Movement between stores
    """
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"

def create_response(status_code, body):
    """Creates a standardized API response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }

def validate_fields(data, required_fields):
    """Validates that all required fields are present in the data."""
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.warning("Missing required fields", extra={"missing_fields": missing_fields})
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

@log_request
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """Main Lambda handler that routes requests to appropriate functions."""
    try:
        function_name = os.getenv('FUNCTION_NAME')
        logger.info("Processing request", extra={
            "function": function_name,
            "request_id": context.aws_request_id
        })
        
        handler_function = function_map.get(function_name)
        if not handler_function:
            logger.error("Invalid function name", extra={"function_name": function_name})
            return create_response(400, {"message": "Invalid function name"})
        
        return handler_function(event, context)
        
    except Exception as e:
        logger.exception("Unexpected error", extra={"error": str(e)})
        return create_response(500, {"message": "Internal server error"})

# Product Management Functions
@log_request
def list_products(event: dict, context: LambdaContext) -> dict:
    """Lists all products in the system."""
    try:
        logger.info("Retrieving all products")
        products = list(db.products.find({}, {
            '_id': 1, 
            'name': 1, 
            'description': 1, 
            'category': 1, 
            'price': 1, 
            'sku': 1
        }))
        
        for product in products:
            product["id"] = str(product.pop("_id"))
            
        logger.info("Products retrieved successfully", extra={"count": len(products)})
        return create_response(200, products)
        
    except Exception as e:
        logger.exception("Error retrieving products", extra={"error": str(e)})
        return create_response(500, {"message": "Error retrieving products"})

@log_request
def get_product(event: dict, context: LambdaContext) -> dict:
    """Gets a specific product by ID."""
    try:
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            logger.warning("Missing product ID")
            return create_response(400, {"message": "Product ID is required"})

        logger.info("Retrieving product", extra={"product_id": product_id})
        
        try:
            product = db.products.find_one({"_id": ObjectId(product_id)})
        except:
            logger.warning("Invalid product ID format", extra={"product_id": product_id})
            return create_response(400, {"message": "Invalid product ID format"})

        if not product:
            logger.warning("Product not found", extra={"product_id": product_id})
            return create_response(404, {"message": "Product not found"})

        product["id"] = str(product.pop("_id"))
        
        logger.info("Product retrieved successfully", extra={"product_id": product_id})
        return create_response(200, product)
        
    except Exception as e:
        logger.exception("Error retrieving product", extra={"error": str(e)})
        return create_response(500, {"message": "Error retrieving product"})

@log_request
def create_product(event: dict, context: LambdaContext) -> dict:
    """Creates a new product."""
    try:
        if isinstance(event.get('body'), str):
            product_data = json.loads(event['body'])
        else:
            product_data = event.get('body', {})
            
        logger.info("Creating new product", extra={"product_data": product_data})
        
        required_fields = ['name', 'sku', 'price']
        validate_fields(product_data, required_fields)
        
        existing_product = db.products.find_one({"sku": product_data['sku']})
        if existing_product:
            logger.warning("Duplicate SKU", extra={"sku": product_data['sku']})
            return create_response(400, {"message": "SKU already exists"})
        
        result = db.products.insert_one(product_data)
        
        logger.info("Product created successfully", extra={
            "product_id": str(result.inserted_id),
            "sku": product_data['sku']
        })
        
        return create_response(201, {
            "message": "Product created successfully",
            "id": str(result.inserted_id)
        })
        
    except ValueError as e:
        logger.warning("Invalid product data", extra={"error": str(e)})
        return create_response(400, {"message": str(e)})
    except Exception as e:
        logger.exception("Error creating product", extra={"error": str(e)})
        return create_response(500, {"message": "Error creating product"})

@log_request
def update_product(event: dict, context: LambdaContext) -> dict:
    """Updates an existing product."""
    try:
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            logger.warning("Missing product ID")
            return create_response(400, {"message": "Product ID is required"})

        if isinstance(event.get('body'), str):
            update_data = json.loads(event['body'])
        else:
            update_data = event.get('body', {})
            
        logger.info("Updating product", extra={
            "product_id": product_id,
            "update_data": update_data
        })
        
        try:
            result = db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": update_data}
            )
        except:
            logger.warning("Invalid product ID format", extra={"product_id": product_id})
            return create_response(400, {"message": "Invalid product ID format"})

        if result.matched_count == 0:
            logger.warning("Product not found", extra={"product_id": product_id})
            return create_response(404, {"message": "Product not found"})
            
        logger.info("Product updated successfully", extra={
            "product_id": product_id,
            "modified_count": result.modified_count
        })
        return create_response(200, {"message": "Product updated successfully"})
        
    except Exception as e:
        logger.exception("Error updating product", extra={"error": str(e)})
        return create_response(500, {"message": "Error updating product"})

@log_request
def delete_product(event: dict, context: LambdaContext) -> dict:
    """Deletes a product by ID."""
    try:
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            logger.warning("Missing product ID")
            return create_response(400, {"message": "Product ID is required"})

        logger.info("Deleting product", extra={"product_id": product_id})
        
        try:
            result = db.products.delete_one({"_id": ObjectId(product_id)})
        except:
            logger.warning("Invalid product ID format", extra={"product_id": product_id})
            return create_response(400, {"message": "Invalid product ID format"})

        if result.deleted_count == 0:
            logger.warning("Product not found", extra={"product_id": product_id})
            return create_response(404, {"message": "Product not found"})

        logger.info("Product deleted successfully", extra={"product_id": product_id})
        return create_response(200, {"message": "Product deleted successfully"})
        
    except Exception as e:
        logger.exception("Error deleting product", extra={"error": str(e)})
        return create_response(500, {"message": "Error deleting product"})

# Inventory Management Functions
@log_request
def create_inventory(event: dict, context: LambdaContext) -> dict:
    """Creates a new inventory entry."""
    try:
        if isinstance(event.get('body'), str):
            inventory_data = json.loads(event['body'])
        else:
            inventory_data = event.get('body', {})
            
        logger.info("Creating inventory entry", extra={"inventory_data": inventory_data})
        
        required_fields = ['productId', 'storeId', 'quantity', 'minStock']
        validate_fields(inventory_data, required_fields)
        
        # Validate product exists
        try:
            product = db.products.find_one({"_id": ObjectId(inventory_data['productId'])})
            if not product:
                logger.warning("Product not found", extra={"product_id": inventory_data['productId']})
                return create_response(404, {"message": "Product not found"})
        except:
            logger.warning("Invalid product ID format", extra={"product_id": inventory_data['productId']})
            return create_response(400, {"message": "Invalid product ID format"})
        
        inventory_data['createdAt'] = datetime.utcnow()
        result = db.inventory.insert_one(inventory_data)
        
        logger.info("Inventory entry created successfully", extra={
            "inventory_id": str(result.inserted_id)
        })
        
        return create_response(201, {
            "message": "Inventory entry created successfully",
            "id": str(result.inserted_id)
        })
        
    except ValueError as e:
        logger.warning("Invalid inventory data", extra={"error": str(e)})
        return create_response(400, {"message": str(e)})
    except Exception as e:
        logger.exception("Error creating inventory entry", extra={"error": str(e)})
        return create_response(500, {"message": "Error creating inventory entry"})

@log_request
def get_store_inventory(event: dict, context: LambdaContext) -> dict:
    """Gets inventory for a specific store."""
    try:
        store_id = event.get('pathParameters', {}).get('id')
        if not store_id:
            logger.warning("Missing store ID")
            return create_response(400, {"message": "Store ID is required"})

        logger.info("Retrieving store inventory", extra={"store_id": store_id})
        
        pipeline = [
            {"$match": {"storeId": store_id}},
            {
                "$lookup": {
                    "from": "products",
                    "localField": "productId",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "quantity": 1,
                    "minStock": 1,
                    "product.name": 1,
                    "product.sku": 1,
                    "product.price": 1,
                    "_id": 0
                }
            }
        ]
        
        inventory = list(db.inventory.aggregate(pipeline))
        
        logger.info("Store inventory retrieved successfully", extra={
            "store_id": store_id,
            "count": len(inventory)
        })
        return create_response(200, inventory)
        
    except Exception as e:
        logger.exception("Error retrieving store inventory", extra={"error": str(e)})
        return create_response(500, {"message": "Error retrieving store inventory"})

@log_request
def transfer_stock(event: dict, context: LambdaContext) -> dict:
    """Transfers stock between stores."""
    try:
        if isinstance(event.get('body'), str):
            transfer_data = json.loads(event['body'])
        else:
            transfer_data = event.get('body', {})
            
        logger.info("Processing stock transfer", extra={"transfer_data": transfer_data})
        
        required_fields = ['productId', 'sourceStoreId', 'targetStoreId', 'quantity']
        validate_fields(transfer_data, required_fields)
        
        # Validate quantity is positive
        if transfer_data['quantity'] <= 0:
            logger.warning("Invalid quantity", extra={"quantity": transfer_data['quantity']})
            return create_response(400, {"message": "Quantity must be positive"})
        
        # Check source store has enough stock
        source_inventory = db.inventory.find_one({
            "productId": ObjectId(transfer_data['productId']),
            "storeId": transfer_data['sourceStoreId']
        })
        
        if not source_inventory or source_inventory['quantity'] < transfer_data['quantity']:
            logger.warning("Insufficient stock", extra={
                "store_id": transfer_data['sourceStoreId'],
                "product_id": transfer_data['productId']
            })
            return create_response(400, {"message": "Insufficient stock"})
        
        # Perform transfer
        db.inventory.update_one(
            {
                "productId": ObjectId(transfer_data['productId']),
                "storeId": transfer_data['sourceStoreId']
            },
            {"$inc": {"quantity": -transfer_data['quantity']}}
        )
        
        db.inventory.update_one(
            {
                "productId": ObjectId(transfer_data['productId']),
                "storeId": transfer_data['targetStoreId']
            },
            {
                "$inc": {"quantity": transfer_data['quantity']},
                "$setOnInsert": {
                    "minStock": source_inventory['minStock'],
                    "createdAt": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        # Record movement
        movement = {
            "type": MovementType.TRANSFER.value,
            "productId": ObjectId(transfer_data['productId']),
            "sourceStoreId": transfer_data['sourceStoreId'],
            "targetStoreId": transfer_data['targetStoreId'],
            "quantity": transfer_data['quantity'],
            "timestamp": datetime.utcnow()
        }
        db.movements.insert_one(movement)
        
        logger.info("Stock transfer completed successfully", extra={
            "source_store": transfer_data['sourceStoreId'],
            "target_store": transfer_data['targetStoreId'],
            "quantity": transfer_data['quantity']
        })
        
        return create_response(200, {"message": "Stock transfer completed successfully"})
        
    except ValueError as e:
        logger.warning("Invalid transfer data", extra={"error": str(e)})
        return create_response(400, {"message": str(e)})
    except Exception as e:
        logger.exception("Error processing stock transfer", extra={"error": str(e)})
        return create_response(500, {"message": "Error processing stock transfer"})

@log_request
def get_stock_alerts(event: dict, context: LambdaContext) -> dict:
    """Gets low stock alerts."""
    try:
        logger.info("Retrieving low stock alerts")
        
        pipeline = [
            {
                "$match": {
                    "$expr": {"$lte": ["$quantity", "$minStock"]}
                }
            },
            {
                "$lookup": {
                    "from": "products",
                    "localField": "productId",
                    "foreignField": "_id",
                    "as": "product"
                }
            },
            {"$unwind": "$product"},
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "storeId": 1,
                    "quantity": 1,
                    "minStock": 1,
                    "product.name": 1,
                    "product.sku": 1,
                    "_id": 0
                }
            }
        ]
        
        alerts = list(db.inventory.aggregate(pipeline))
        
        logger.info("Low stock alerts retrieved successfully", extra={"count": len(alerts)})
        return create_response(200, alerts)
        
    except Exception as e:
        logger.exception("Error retrieving stock alerts", extra={"error": str(e)})
        return create_response(500, {"message": "Error retrieving stock alerts"})

# Function mapping for routing
function_map = {
    "ProductList": list_products,
    "ProductGet": get_product,
    "ProductCreate": create_product,
    "ProductUpdate": update_product,
    "ProductDelete": delete_product,
    "InventoryCreate": create_inventory,
    "StockInventory": get_store_inventory,
    "StockTransfer": transfer_stock,
    "StockAlerts": get_stock_alerts
}
