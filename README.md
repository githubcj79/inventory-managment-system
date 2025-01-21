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
pip install -e .

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

1. For unit tests:
# Run all unit tests with coverage
pytest tests/unit/

# Run specific unit test file
pytest tests/unit/test_product_service.py
pytest tests/unit/test_inventory_service.py
pytest tests/unit/test_movement_service.py

2. For integration tests:
# Run the API integration tests
./tests/integration/api/test_api.sh

3. To simplify test execution
make test-unit         # Run only unit tests
make test-integration  # Run only integration tests
make test             # Run all tests

## Project Structure

.
├── docker-compose.yml
├── Dockerfile
├── docs
│   └── Ejercicio 1 - Sistema de Gestion de Inventario.pdf
├── makefile
├── Notes.md
├── pytest.ini
├── README.md
├── requirements.txt
├── scripts
│   └── init_db.py
├── src
│   ├── app.py
│   ├── common
│   │   ├── db_utils.py
│   │   └── __init__.py
│   ├── __init__.py
│   └── requirements.txt
├── template.yaml
└── tests
    ├── __init__.py
    ├── integration
    │   ├── api
    │   │   └── test_api.sh
    │   ├── conftest.py
    │   └── __init__.py
    └── unit
        ├── conftest.py
        ├── __init__.py
        ├── test_inventory_service.py
        ├── test_movement_service.py
        └── test_product_service.py

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

