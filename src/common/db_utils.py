# common/db_utils.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from aws_lambda_powertools import Logger
import os
import sys

# Initialize logger
logger = Logger(service="inventory-management", child=True)

def get_mongo_client():
    try:
        # Get MongoDB URI from environment variables
        mongo_uri = os.getenv("MONGO_DB_URI")
        
        if not mongo_uri:
            logger.error("MONGO_DB_URI environment variable is not set", 
                        extra={"environment_variables": dict(os.environ)})
            raise ValueError("MONGO_DB_URI environment variable is not set")

        logger.info("Attempting to connect to MongoDB", 
                   extra={"mongodb_uri": mongo_uri})
        
        # Create MongoDB client with timeout settings
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,  # Reduced timeout for faster feedback
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test the connection
        try:
            logger.debug("Testing MongoDB connection...")
            client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            return client
        except ConnectionFailure as cf:
            logger.error("Server not available", 
                        extra={"error": str(cf)})
            raise
        except ServerSelectionTimeoutError as sste:
            logger.error("Server selection timeout - MongoDB server is not reachable", 
                        extra={"error": str(sste)})
            raise

    except Exception as e:
        logger.error("Failed to connect to MongoDB", 
                    extra={
                        "error": str(e),
                        "cwd": os.getcwd(),
                        "python_path": sys.path,
                        "mongodb_uri": mongo_uri
                    })
        
        # Check if MongoDB is accessible on the network
        import socket
        try:
            host = mongo_uri.split('@')[-1].split(':')[0] if '@' in mongo_uri else mongo_uri.split('//')[1].split(':')[0]
            port = int(mongo_uri.split(':')[-1].split('/')[0]) if ':' in mongo_uri else 27017
            
            logger.debug("Checking MongoDB port accessibility", 
                        extra={"host": host, "port": port})
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.info("MongoDB port is accessible", 
                           extra={"host": host, "port": port})
            else:
                logger.error("MongoDB port is not accessible", 
                            extra={"host": host, "port": port})
            sock.close()
        except Exception as socket_error:
            logger.error("Error checking MongoDB port", 
                        extra={"error": str(socket_error)})
        
        raise
