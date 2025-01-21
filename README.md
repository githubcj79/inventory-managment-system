# Inventory Management System

A serverless inventory management system built with AWS SAM, Python, and MongoDB. This system helps manage product inventory across multiple stores, handling stock transfers, and providing low stock alerts.

## Features

- Product Management (CRUD operations)
- Multi-store Inventory Tracking
- Stock Transfer Between Stores
- Low Stock Alerts
- Movement History Tracking
- RESTful API Interface

## Tech Stack

- **Backend**: Python 3.9+
- **Framework**: AWS SAM (Serverless Application Model)
- **Database**: MongoDB
- **Container**: Docker
- **API**: REST API with AWS API Gateway
- **Testing**: Shell Script for API Testing

## Prerequisites

- Python 3.9 or higher
- AWS SAM CLI
- Docker
- MongoDB
- Git

## Local Development Setup

1. Clone the repository:
git clone <https://github.com/githubcj79/inventory-managment-system.git>
cd inventory-managment-system

2. Create and activate virtual environment:
python -m venv .venv
source .venv/bin/activate  # For Unix/MacOS
# or
.venv\Scripts\activate  # For Windows

3. Install dependencies:
pip install -r requirements.txt

4. Start MongoDB using Docker:
docker-compose up -d

5. Run the initialization script:
python scripts/init_db.py

6. Build the SAM application:
sam build

7. Start the local API:
sam local start-api --docker-network inventory-managment-system_backend

## API Endpoints

- `GET /api/products` - List all products
- `GET /api/products/{id}` - Get product details
- `POST /api/products` - Create new product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product
- `POST /api/inventory` - Create initial inventory
- `GET /api/stores/{id}/inventory` - List store inventory
- `POST /api/inventory/transfer` - Transfer stock between stores
- `GET /api/inventory/alert` - Get low stock alerts

## Testing

Run the API tests:
chmod +x tests/test_api.sh
./tests/test_api.sh

## Project Structure

.
├── docker-compose.yml      # Docker compose configuration
├── Dockerfile             # Docker build file
├── docs/                  # Documentation files
├── env.json              # Environment configuration
├── requirements.txt      # Python dependencies
├── src/                  # Source code
│   ├── app.py           # Main application code
│   └── common/          # Shared utilities
├── template.yaml        # SAM template
└── tests/              # Test files

## Environment Variables (defined in template.yaml)

Required environment variables:
- `MONGODB_URI`: MongoDB connection string
- `FUNCTION_NAME`: AWS Lambda function name

## Data Models

### Product
- `id`: ObjectId
- `name`: String
- `description`: String
- `category`: String
- `price`: Number
- `sku`: String (unique)

### Inventory
- `productId`: ObjectId
- `storeId`: String
- `quantity`: Number
- `minStock`: Number

### Movement
- `productId`: ObjectId
- `sourceStoreId`: String
- `targetStoreId`: String
- `quantity`: Number
- `timestamp`: DateTime
- `type`: Enum(IN, OUT, TRANSFER)

