import os
from pymongo import MongoClient
from pymongo.errors import OperationFailure
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_indexes(mongodb_uri):
    """Create MongoDB indexes for optimizing frequent operations."""
    client = MongoClient(mongodb_uri)
    db = client.inventory_db
    
    try:
        # Product indexes
        logger.info("Creating product indexes...")
        db.products.create_index([("sku", 1)], unique=True)
        db.products.create_index([("name", 1)])
        db.products.create_index([("category", 1)])
        
        # Inventory indexes
        logger.info("Creating inventory indexes...")
        db.inventory.create_index([
            ("productId", 1),
            ("storeId", 1)
        ], unique=True)
        db.inventory.create_index([("storeId", 1)])
        db.inventory.create_index([("quantity", 1)])
        db.inventory.create_index([
            ("quantity", 1),
            ("minStock", 1)
        ])
        
        # Movement indexes
        logger.info("Creating movement indexes...")
        db.movement.create_index([("productId", 1)])
        db.movement.create_index([("timestamp", -1)])
        db.movement.create_index([
            ("sourceStoreId", 1),
            ("timestamp", -1)
        ])
        db.movement.create_index([
            ("targetStoreId", 1),
            ("timestamp", -1)
        ])
        db.movement.create_index([
            ("type", 1),
            ("timestamp", -1)
        ])
        
        logger.info("Successfully created all indexes")
        
    except OperationFailure as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise
    finally:
        client.close()

def main():
    """Main function to set up MongoDB indexes."""
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    
    try:
        logger.info(f"Connecting to MongoDB at {mongodb_uri}")
        setup_indexes(mongodb_uri)
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
