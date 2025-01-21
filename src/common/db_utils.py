# common/db_utils.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
import sys

def get_mongo_client():
    try:
        # Get MongoDB URI from environment variables
        mongo_uri = os.getenv("MONGO_DB_URI")
        
        if not mongo_uri:
            print("MONGO_DB_URI environment variable is not set", file=sys.stderr)
            print(f"Available environment variables: {dict(os.environ)}", file=sys.stderr)
            raise ValueError("MONGO_DB_URI environment variable is not set")

        print(f"Attempting to connect to MongoDB at: {mongo_uri}", file=sys.stderr)
        
        # Create MongoDB client with timeout settings
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,  # Reduced timeout for faster feedback
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
        
        # Test the connection
        try:
            print("Testing MongoDB connection...", file=sys.stderr)
            client.admin.command('ping')
            print("Successfully connected to MongoDB", file=sys.stderr)
            return client
        except ConnectionFailure as cf:
            print(f"Server not available: {str(cf)}", file=sys.stderr)
            raise
        except ServerSelectionTimeoutError as sste:
            print(f"Server selection timeout: {str(sste)}", file=sys.stderr)
            print("This often means the MongoDB server is not reachable", file=sys.stderr)
            raise

    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}", file=sys.stderr)
        print(f"Current working directory: {os.getcwd()}", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        print(f"MongoDB URI: {mongo_uri}", file=sys.stderr)
        
        # Check if MongoDB is accessible on the network
        import socket
        try:
            host = mongo_uri.split('@')[-1].split(':')[0] if '@' in mongo_uri else mongo_uri.split('//')[1].split(':')[0]
            port = int(mongo_uri.split(':')[-1].split('/')[0]) if ':' in mongo_uri else 27017
            
            print(f"Attempting to check if MongoDB port is accessible at {host}:{port}", file=sys.stderr)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            if result == 0:
                print(f"Port {port} is open on {host}", file=sys.stderr)
            else:
                print(f"Port {port} is not accessible on {host}", file=sys.stderr)
            sock.close()
        except Exception as socket_error:
            print(f"Error checking MongoDB port: {str(socket_error)}", file=sys.stderr)
        
        raise
