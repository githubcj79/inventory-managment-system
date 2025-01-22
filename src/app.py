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

The API uses AWS Lambda functions through AWS SAM for serverless deployment.
"""

import json
import os
from datetime import datetime
from bson import ObjectId
from common.db_utils import get_mongo_client
from enum import Enum

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


def lambda_handler(event, context):
    """
    Main Lambda handler that routes requests to appropriate functions.

    Args:
        event (dict): AWS Lambda event object
        context (object): AWS Lambda context object

    Returns:
        dict: API Gateway response object
    """
    # Define function mapping dictionary
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
    
    try:
        function_name = os.getenv('FUNCTION_NAME')
        handler_function = function_map.get(function_name)
        
        if handler_function:
            return handler_function(event)
        
        return create_response(400, {"message": "Invalid function name"})
    
    except ValueError as e:
        return create_response(400, {"message": str(e)})
    except Exception as e:
        print(f"Error: {str(e)}")
        return create_response(500, {"message": "Internal server error"})


def list_products(event):
    """
    Lists all products in the system.

    Args:
        event (dict): API Gateway event object

    Returns:
        dict: Response with list of products
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    products = list(db.products.find({}, {'_id': 1, 'name': 1, 'description': 1, 
                                        'category': 1, 'price': 1, 'sku': 1}))
    for product in products:
        product["id"] = str(product.pop("_id"))
    return create_response(200, products)

def get_product(event):
    """
    Gets a specific product by ID.

    Args:
        event (dict): API Gateway event with product ID

    Returns:
        dict: Response with product details or error message
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    product_id = event.get('pathParameters', {}).get('id')
    if not product_id:
        return create_response(400, {"message": "Product ID is required"})

    try:
        product = db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            return create_response(404, {"message": "Product not found"})
        
        product["id"] = str(product.pop("_id"))
        return create_response(200, product)
    except:
        return create_response(400, {"message": "Invalid product ID format"})

def create_product(event):
    """
    Creates a new product.

    Args:
        event (dict): API Gateway event with product data

    Returns:
        dict: Response with creation status
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    if isinstance(event.get('body'), str):
        product_data = json.loads(event['body'])
    else:
        product_data = event.get('body', {})

    validate_fields(product_data, ['name', 'description', 'category', 'price', 'sku'])
    
    if db.products.find_one({"sku": product_data["sku"]}):
        return create_response(400, {"message": "SKU already exists"})
    
    result = db.products.insert_one(product_data)
    return create_response(201, {
        "message": "Product created successfully",
        "id": str(result.inserted_id)
    })

def update_product(event):
    """
    Updates an existing product.

    Args:
        event (dict): API Gateway event with product ID and update data

    Returns:
        dict: Response with update status
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    product_id = event.get('pathParameters', {}).get('id')
    if not product_id:
        return create_response(400, {"message": "Product ID is required"})

    if isinstance(event.get('body'), str):
        updated_data = json.loads(event['body'])
    else:
        updated_data = event.get('body', {})

    valid_fields = {'name', 'description', 'category', 'price', 'sku'}
    update_data = {k: v for k, v in updated_data.items() if k in valid_fields}

    if 'sku' in update_data:
        existing = db.products.find_one({
            "sku": update_data["sku"],
            "_id": {"$ne": ObjectId(product_id)}
        })
        if existing:
            return create_response(400, {"message": "SKU already exists"})

    result = db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )

    if result.matched_count == 0:
        return create_response(404, {"message": "Product not found"})

    return create_response(200, {"message": "Product updated successfully"})

def delete_product(event):
    """
    Deletes a product if it has no associated inventory.

    Args:
        event (dict): API Gateway event with product ID

    Returns:
        dict: Response with deletion status
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    product_id = event.get('pathParameters', {}).get('id')
    if not product_id:
        return create_response(400, {"message": "Product ID is required"})

    if db.inventory.find_one({"productId": product_id}):
        return create_response(400, {"message": "Cannot delete product with existing inventory"})

    result = db.products.delete_one({"_id": ObjectId(product_id)})
    
    if result.deleted_count == 0:
        return create_response(404, {"message": "Product not found"})
        
    return create_response(200, {"message": "Product deleted successfully"})

def create_inventory(event):
    """
    Creates initial inventory for a product in a store.

    Args:
        event (dict): API Gateway event with inventory data

    Returns:
        dict: Response with creation status
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    if isinstance(event.get('body'), str):
        inventory_data = json.loads(event['body'])
    else:
        inventory_data = event.get('body', {})

    validate_fields(inventory_data, ['productId', 'storeId', 'quantity', 'minStock'])
    
    try:
        inventory_data['productId'] = ObjectId(inventory_data['productId'])
    except:
        return create_response(400, {"message": "Invalid product ID format"})

    product = db.products.find_one({"_id": inventory_data["productId"]})
    if not product:
        return create_response(404, {"message": "Product not found"})

    existing = db.inventory.find_one({
        "productId": inventory_data["productId"],
        "storeId": inventory_data["storeId"]
    })
    
    if existing:
        return create_response(400, {"message": "Inventory already exists for this product and store"})

    result = db.inventory.insert_one(inventory_data)
    
    movement_data = {
        "productId": inventory_data["productId"],
        "sourceStoreId": None,
        "targetStoreId": inventory_data["storeId"],
        "quantity": inventory_data["quantity"],
        "timestamp": datetime.utcnow(),
        "type": MovementType.IN.value
    }
    db.movements.insert_one(movement_data)

    return create_response(201, {
        "message": "Inventory created successfully",
        "id": str(result.inserted_id)
    })

def list_inventory(event):
    """
    Lists inventory for a specific store with product details.

    Args:
        event (dict): API Gateway event with store ID

    Returns:
        dict: Response with inventory list
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    store_id = event.get('pathParameters', {}).get('id')
    if not store_id:
        return create_response(400, {"message": "Store ID is required"})

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
                "_id": 1,
                "quantity": 1,
                "minStock": 1,
                "storeId": 1,
                "product": {
                    "_id": 1,
                    "name": 1,
                    "sku": 1,
                    "price": 1
                }
            }
        }
    ]
    
    inventory = list(db.inventory.aggregate(pipeline))
    for item in inventory:
        item["id"] = str(item.pop("_id"))
        item["product"]["id"] = str(item["product"].pop("_id"))
    
    return create_response(200, inventory)

def transfer_stock(event):
    """
    Transfers stock between stores.

    Args:
        event (dict): API Gateway event with transfer details

    Returns:
        dict: Response with transfer status
    """
    client = get_mongo_client()
    db = client["inventory_management"]
    
    if isinstance(event.get('body'), str):
        transfer_data = json.loads(event['body'])
    else:
        transfer_data = event.get('body', {})

    validate_fields(transfer_data, ['productId', 'sourceStoreId', 'targetStoreId', 'quantity'])

    if transfer_data["sourceStoreId"] == transfer_data["targetStoreId"]:
        return create_response(400, {"message": "Source and target stores must be different"})

    try:
        transfer_data['productId'] = ObjectId(transfer_data['productId'])
    except:
        return create_response(400, {"message": "Invalid product ID format"})

    source_inventory = db.inventory.find_one({
        "storeId": transfer_data["sourceStoreId"],
        "productId": transfer_data["productId"]
    })

    if not source_inventory or source_inventory["quantity"] < transfer_data["quantity"]:
        return create_response(400, {"message": "Insufficient stock in source store"})

    # Update source store inventory
    db.inventory.update_one(
        {
            "storeId": transfer_data["sourceStoreId"],
            "productId": transfer_data["productId"]
        },
        {"$inc": {"quantity": -transfer_data["quantity"]}}
    )

    # Update or create target store inventory
    db.inventory.update_one(
        {
            "storeId": transfer_data["targetStoreId"],
            "productId": transfer_data["productId"]
        },
        {
            "$inc": {"quantity": transfer_data["quantity"]},
            "$setOnInsert": {"minStock": source_inventory["minStock"]}
        },
        upsert=True
    )

    # Record movement
    movement_data = {
        "productId": transfer_data["productId"],
        "sourceStoreId": transfer_data["sourceStoreId"],
        "targetStoreId": transfer_data["targetStoreId"],
        "quantity": transfer_data["quantity"],
        "timestamp": datetime.utcnow(),
        "type": MovementType.TRANSFER.value
    }
    db.movements.insert_one(movement_data)

    return create_response(200, {"message": "Stock transferred successfully"})

def low_stock_alerts(event):
    """
    Retrieves list of products with stock below minimum level.

    Args:
        event (dict): API Gateway event

    Returns:
        dict: Response with list of low stock items
    """
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
                "_id": 1,
                "quantity": 1,
                "minStock": 1,
                "storeId": 1,
                "product": {
                    "_id": 1,
                    "name": 1,
                    "sku": 1,
                    "price": 1
                }
            }
        }
    ]
    
    low_stock = list(db.inventory.aggregate(pipeline))
    
    for item in low_stock:
        item["id"] = str(item.pop("_id"))
        item["product"]["id"] = str(item["product"].pop("_id"))
        
    return create_response(200, low_stock)
