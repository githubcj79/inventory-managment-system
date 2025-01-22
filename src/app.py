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

logger = Logger(service="inventory-management")

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
    """
    Creates a standardized API response.

    Args:
        status_code (int): HTTP status code
        body (dict): Response payload

    Returns:
        dict: Formatted response with headers and body
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, default=str)
    }

def validate_fields(data, required_fields):
    """
    Validates that all required fields are present in the data.

    Args:
        data (dict): Input data to validate
        required_fields (list): List of required field names

    Raises:
        ValueError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

@log_request
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    """
    Main Lambda handler that routes requests to appropriate functions.

    Args:
        event (dict): AWS Lambda event object
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: API Gateway response object
    """
    try:
        function_name = os.getenv('FUNCTION_NAME')
        logger.info("Processing request", extra={"function": function_name})
        
        handler_function = function_map.get(function_name)
        if not handler_function:
            logger.error("Invalid function name", extra={"function_name": function_name})
            return create_response(400, {"message": "Invalid function name"})
        
        return handler_function(event, context)
        
    except Exception as e:
        logger.exception("Unexpected error")
        return create_response(500, {"message": "Internal server error"})

@log_request
def list_products(event: dict, context: LambdaContext) -> dict:
    """
    Lists all products in the system.

    Args:
        event (dict): API Gateway event object
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with list of products
    """
    try:
        logger.info("Retrieving all products")
        client = get_mongo_client()
        db = client["inventory_management"]
        
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
        logger.exception("Error retrieving products")
        return create_response(500, {"message": "Error retrieving products"})

@log_request
def get_product(event: dict, context: LambdaContext) -> dict:
    """
    Gets a specific product by ID.

    Args:
        event (dict): API Gateway event with product ID
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with product details
    """
    try:
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            logger.warning("Missing product ID")
            return create_response(400, {"message": "Product ID is required"})

        logger.info("Retrieving product", extra={"product_id": product_id})
        client = get_mongo_client()
        db = client["inventory_management"]
        
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
        logger.exception("Error retrieving product")
        return create_response(500, {"message": "Error retrieving product"})

@log_request
def create_product(event: dict, context: LambdaContext) -> dict:
    """
    Creates a new product.

    Args:
        event (dict): API Gateway event with product data
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with creation status
    """
    try:
        if isinstance(event.get('body'), str):
            product_data = json.loads(event['body'])
        else:
            product_data = event.get('body', {})
            
        logger.info("Creating new product", extra={"product_data": product_data})
        
        required_fields = ['name', 'sku', 'price']
        validate_fields(product_data, required_fields)
        
        client = get_mongo_client()
        db = client["inventory_management"]
        
        # Check if SKU already exists
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
        logger.exception("Error creating product")
        return create_response(500, {"message": "Error creating product"})

@log_request
def update_product(event: dict, context: LambdaContext) -> dict:
    """
    Updates an existing product.

    Args:
        event (dict): API Gateway event with product data
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with update status
    """
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
        
        client = get_mongo_client()
        db = client["inventory_management"]
        
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
            
        logger.info("Product updated successfully", extra={"product_id": product_id})
        return create_response(200, {"message": "Product updated successfully"})
        
    except Exception as e:
        logger.exception("Error updating product")
        return create_response(500, {"message": "Error updating product"})

@log_request
def delete_product(event: dict, context: LambdaContext) -> dict:
    """
    Deletes a product.

    Args:
        event (dict): API Gateway event with product ID
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with deletion status
    """
    try:
        product_id = event.get('pathParameters', {}).get('id')
        if not product_id:
            logger.warning("Missing product ID")
            return create_response(400, {"message": "Product ID is required"})

        logger.info("Deleting product", extra={"product_id": product_id})
        
        client = get_mongo_client()
        db = client["inventory_management"]
        
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
        logger.exception("Error deleting product")
        return create_response(500, {"message": "Error deleting product"})

@log_request
def create_inventory(event: dict, context: LambdaContext) -> dict:
    """
    Creates initial inventory for a product in a store.

    Args:
        event (dict): API Gateway event with inventory data
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with creation status
    """
    try:
        if isinstance(event.get('body'), str):
            inventory_data = json.loads(event['body'])
        else:
            inventory_data = event.get('body', {})
            
        logger.info("Creating inventory", extra={"inventory_data": inventory_data})
        
        required_fields = ['productId', 'storeId', 'quantity', 'minStock']
        validate_fields(inventory_data, required_fields)
        
        client = get_mongo_client()
        db = client["inventory_management"]
        
        try:
            inventory_data['productId'] = ObjectId(inventory_data['productId'])
        except:
            logger.warning("Invalid product ID format", extra={"product_id": inventory_data.get('productId')})
            return create_response(400, {"message": "Invalid product ID format"})
            
        # Create inventory record
        inventory_data['createdAt'] = datetime.utcnow()
        result = db.inventory.insert_one(inventory_data)
        
        # Record movement
        movement = {
            "productId": inventory_data['productId'],
            "storeId": inventory_data['storeId'],
            "quantity": inventory_data['quantity'],
            "type": MovementType.IN.value,
            "timestamp": datetime.utcnow()
        }
        db.movements.insert_one(movement)
        
        logger.info("Inventory created successfully", extra={
            "inventory_id": str(result.inserted_id),
            "product_id": str(inventory_data['productId'])
        })
        
        return create_response(201, {
            "message": "Inventory created successfully",
            "id": str(result.inserted_id)
        })
        
    except ValueError as e:
        logger.warning("Invalid inventory data", extra={"error": str(e)})
        return create_response(400, {"message": str(e)})
    except Exception as e:
        logger.exception("Error creating inventory")
        return create_response(500, {"message": "Error creating inventory"})

@log_request
def list_inventory(event: dict, context: LambdaContext) -> dict:
    """
    Lists inventory for a specific store.

    Args:
        event (dict): API Gateway event with store ID
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with inventory list
    """
    try:
        store_id = event.get('pathParameters', {}).get('id')
        if not store_id:
            logger.warning("Missing store ID")
            return create_response(400, {"message": "Store ID is required"})
            
        logger.info("Retrieving store inventory", extra={"store_id": store_id})

        client = get_mongo_client()
        db = client["inventory_management"]
        
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
                    "productId": {"$toString": "$productId"},
                    "productName": "$product.name",
                    "sku": "$product.sku",
                    "quantity": 1,
                    "minStock": 1,
                    "storeId": 1,
                    "_id": 0
                }
            }
        ]
        
        inventory = list(db.inventory.aggregate(pipeline))
        
        logger.info("Inventory retrieved successfully", extra={
            "store_id": store_id,
            "count": len(inventory)
        })
        
        return create_response(200, inventory)
        
    except Exception as e:
        logger.exception("Error retrieving inventory")
        return create_response(500, {"message": "Error retrieving inventory"})

@log_request
def transfer_stock(event: dict, context: LambdaContext) -> dict:
    """
    Transfers stock between stores.

    Args:
        event (dict): API Gateway event with transfer details
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with transfer status
    """
    try:
        if isinstance(event.get('body'), str):
            transfer_data = json.loads(event['body'])
        else:
            transfer_data = event.get('body', {})
            
        logger.info("Processing stock transfer", extra={"transfer_data": transfer_data})

        required_fields = ['productId', 'sourceStoreId', 'targetStoreId', 'quantity']
        validate_fields(transfer_data, required_fields)

        try:
            product_id = ObjectId(transfer_data['productId'])
        except:
            logger.warning("Invalid product ID format", extra={"product_id": transfer_data['productId']})
            return create_response(400, {"message": "Invalid product ID format"})

        if transfer_data['sourceStoreId'] == transfer_data['targetStoreId']:
            logger.warning("Invalid transfer - same source and target store")
            return create_response(400, {"message": "Source and target stores must be different"})

        client = get_mongo_client()
        db = client["inventory_management"]

        # Check source inventory
        source_inventory = db.inventory.find_one({
            "productId": product_id,
            "storeId": transfer_data['sourceStoreId']
        })
        
        if not source_inventory or source_inventory['quantity'] < transfer_data['quantity']:
            logger.warning("Insufficient stock", extra={
                "source_store": transfer_data['sourceStoreId'],
                "requested_quantity": transfer_data['quantity'],
                "available_quantity": source_inventory['quantity'] if source_inventory else 0
            })
            return create_response(400, {"message": "Insufficient stock in source store"})

        # Update source and target inventory
        db.inventory.update_one(
            {"productId": product_id, "storeId": transfer_data['sourceStoreId']},
            {"$inc": {"quantity": -transfer_data['quantity']}}
        )
        
        db.inventory.update_one(
            {"productId": product_id, "storeId": transfer_data['targetStoreId']},
            {
                "$inc": {"quantity": transfer_data['quantity']},
                "$setOnInsert": {"minStock": source_inventory['minStock']}
            },
            upsert=True
        )

        # Record movement
        movement = {
            "productId": product_id,
            "sourceStoreId": transfer_data['sourceStoreId'],
            "targetStoreId": transfer_data['targetStoreId'],
            "quantity": transfer_data['quantity'],
            "type": MovementType.TRANSFER.value,
            "timestamp": datetime.utcnow()
        }
        db.movements.insert_one(movement)

        logger.info("Stock transfer completed successfully", extra={
            "product_id": str(product_id),
            "quantity": transfer_data['quantity'],
            "source_store": transfer_data['sourceStoreId'],
            "target_store": transfer_data['targetStoreId']
        })
        
        return create_response(200, {"message": "Stock transferred successfully"})
        
    except ValueError as e:
        logger.warning("Invalid transfer data", extra={"error": str(e)})
        return create_response(400, {"message": str(e)})
    except Exception as e:
        logger.exception("Error transferring stock")
        return create_response(500, {"message": "Error transferring stock"})

@log_request
def low_stock_alerts(event: dict, context: LambdaContext) -> dict:
    """
    Lists all products with stock below minimum level.

    Args:
        event (dict): API Gateway event
        context (LambdaContext): AWS Lambda context object

    Returns:
        dict: Response with list of low stock alerts
    """
    try:
        logger.info("Retrieving low stock alerts")
        client = get_mongo_client()
        db = client["inventory_management"]
        
        pipeline = [
            {
                "$match": {
                    "$expr": {"$lt": ["$quantity", "$minStock"]}
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
                    "productId": {"$toString": "$productId"},
                    "productName": "$product.name",
                    "sku": "$product.sku",
                    "storeId": 1,
                    "currentStock": "$quantity",
                    "minStock": 1,
                    "deficit": {"$subtract": ["$minStock", "$quantity"]},
                    "_id": 0
                }
            }
        ]
        
        alerts = list(db.inventory.aggregate(pipeline))
        
        logger.info("Low stock alerts retrieved", extra={"alert_count": len(alerts)})
        return create_response(200, alerts)
        
    except Exception as e:
        logger.exception("Error retrieving low stock alerts")
        return create_response(500, {"message": "Error retrieving low stock alerts"})

# Function mapping for routing
function_map = {
    "ProductList": list_products,
    "ProductGet": get_product,
    "ProductCreate": create_product,
    "ProductUpdate": update_product,
    "ProductDelete": delete_product,
    "InventoryCreate": create_inventory,
    "StockInventory": list_inventory,
    "StockTransfer": transfer_stock,
    "StockAlerts": low_stock_alerts
}
