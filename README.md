
# Inventory Management System API

A RESTful API designed for managing product inventory across multiple stores. Built using AWS SAM, Python, and MongoDB. The system includes functionalities for product management, inventory tracking, stock transfers, and low-stock alerts.

---

## **Core Features**

- **Product Management**: CRUD operations for product lifecycle.
- **Multi-store Inventory Tracking**: Maintain stock levels for each store.
- **Stock Transfer Between Stores**: Facilitate transferring stock between stores.
- **Low Stock Alerts**: Automatically notify when stock reaches below minimum levels.

---

## **Data Models**

### **Product**
```json
{
  "id": "ObjectId",
  "name": "String",
  "description": "String",
  "category": "String",
  "price": "Number",
  "sku": "String (unique)"
}
```

### **Inventory**
```json
{
  "productId": "ObjectId",
  "storeId": "String",
  "quantity": "Number",
  "minStock": "Number"
}
```

### **Movement**
```json
{
  "productId": "ObjectId",
  "sourceStoreId": "String",
  "targetStoreId": "String",
  "quantity": "Number",
  "timestamp": "DateTime",
  "type": "Enum(IN, OUT, TRANSFER)"
}
```

---

## **API Endpoints**

### **Products**

- **GET /products**: Retrieve a list of all products.
- **GET /products/{id}**: Retrieve product details by ID.
- **POST /products**: Create a new product.
- **PUT /products/{id}**: Update an existing product by ID.
- **DELETE /products/{id}**: Delete a product by ID.

### **Inventory**

- **POST /inventory**: Create or update an inventory entry.
- **GET /stores/{id}/inventory**: Get the inventory of a specific store.
- **POST /inventory/transfer**: Transfer stock between stores.
- **GET /inventory/alert**: Get low stock alerts.

---

## **Key Concepts**

- **Product**: Each product has a unique SKU, category, description, and price.
- **Store Inventory**: Independent stock levels for each store.
- **Stock Transfers**: Track stock movements between stores.
- **Low Stock Alerts**: Notifications triggered when a product's stock drops below the minimum threshold.

---

## **Technical Decisions**

- **Lambda Functions Sharing Code**:  
   All 9 Lambda functions in this project share the same code located in the `src/` directory. This is defined in the `template.yaml` file under the **Globals** section, where the `CodeUri` is set to `src/`.  
   The functions behave differently based on the value of the `FUNCTION_NAME` environment variable, allowing a single codebase to handle different logic for each function.

- **Database Connection Optimization**:  
   The database connection is established at the module level for optimization.  
   - **Cold Start**: If the Lambda container is new (cold start), it initializes the database connection.
   - **Warm Start**: If the Lambda container is reused, it doesn't need to reinitialize the connection, as the existing connection is used.
   - The `db` variable is made available to all functions within the module, improving performance by reusing the connection in subsequent invocations.

---

## **Tech Stack**

- **Backend**: Python 3.9+
- **Framework**: AWS SAM (Serverless Application Model)
- **Database**: MongoDB
- **Container**: Docker
- **API**: REST API via AWS API Gateway
- **Testing**: Shell Script for API Testing

---

## **Installation Instructions**

### **Prerequisites**

Ensure the following are installed:

- Python 3.9 or higher
- AWS SAM CLI (to simulate the AWS environment locally)
- Docker (for running MongoDB in a container)
- MongoDB (used in the local development environment)
- Git

### **Local Development Setup**

The development is aimed at deployment in AWS Cloud, and to simulate production conditions locally, we use **SAM CLI** and the **template.yaml** file for infrastructure as code (IaC). The **template.yaml** defines the API Gateway and the AWS Lambda functions associated with the API endpoints.

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/githubcj79/inventory-managment-system.git
   cd inventory-managment-system
   ```

2. **Create and Activate Virtual Environment:**
   - For Unix/MacOS:
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```
   - For Windows:
     ```bash
     python -m venv .venv
     .venv\Scriptsctivate
     ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Start MongoDB Using Docker Compose:**
   Docker Compose is used to run MongoDB in a container and ensure the data is persistent by using a volume.

   - Ensure MongoDB is running in a Docker container:
     ```bash
     docker-compose up -d
     ```
   This command will start MongoDB and create a persistent volume for data storage.

5. **Run Initialization Script:**
   This script sets up the initial database content for local testing:
   ```bash
   python scripts/init_db.py
   ```

6. **Define API and Lambda Functions in `template.yaml`:**

   The **`template.yaml`** file is the backbone of the application's infrastructure. It defines:

   - The **API Gateway** that exposes the RESTful API.
   - The **Lambda functions** that are triggered by each API endpoint.

   The `template.yaml` ensures that your infrastructure is consistently deployed, allowing for easy local testing with SAM CLI. The defined API Gateway and Lambda functions mirror the setup in the cloud, enabling you to test the API locally.

7. **Build the SAM Application:**
   Use SAM CLI to build the application as infrastructure as code:
   ```bash
   sam build
   ```

8. **Start Local API:**
   Start the local version of the API using SAM CLI. This will simulate the AWS environment locally:
   ```bash
   sam local start-api --debug --docker-network inventory-managment-system_backend --log-file ./output.log
   ```

---

## **Testing**

### **Unit Tests**

To run unit tests:

- Run all unit tests with coverage:
  ```bash
  pytest tests/unit/
  ```

- Run specific unit tests:
  ```bash
  pytest tests/unit/test_product_service.py
  pytest tests/unit/test_inventory_service.py
  pytest tests/unit/test_movement_service.py
  ```

### **Integration Tests**

To run integration tests:
1. Make the script executable:
   ```bash
   chmod +x ./tests/integration/api/test_api.sh
   ```

2. Run the integration tests:
   ```bash
   ./tests/integration/api/test_api.sh
   ```

3. Use `make` for simplified execution:
   - Run only unit tests:
     ```bash
     make test-unit
     ```
   - Run only integration tests:
     ```bash
     make test-integration
     ```
   - Run all tests:
     ```bash
     make test
     ```

### **Load Testing**

To perform load testing:

1. **Run Load Tests with Default Parameters:**
   When you run `./tests/load/run_load_tests.sh` without any parameters, it uses these default values:

   - **TARGET_HOST**: `http://localhost:3000/api` – This will test against your local API.
   - **NUM_USERS**: `10` – Simulates 10 concurrent users.
   - **SPAWN_RATE**: `1` – Adds 1 new user per second.
   - **DURATION**: `1m` – The test will run for 1 minute.
   - **CSV_FILE**: `load_test_metrics_[timestamp].csv` – The results will be saved in three different CSV files by default.

   So, the ramp-up would look like this:

   - **At 1 second**: 1 user
   - **At 2 seconds**: 2 users
   - **At 3 seconds**: 3 users
   - **At 4 seconds**: 4 users
   - **At 5 seconds**: 5 users
   - **At 6 seconds**: 6 users
   - **At 7 seconds**: 7 users
   - **At 8 seconds**: 8 users
   - **At 9 seconds**: 9 users
   - **At 10 seconds**: 10 users (target reached)

   After reaching the target of 10 users at 10 seconds, the test will continue running with 10 concurrent users for the remaining 50 seconds to complete the 1-minute duration, and save the results in three timestamped CSV files.

   To run the default load test:
   ```bash
   chmod +x ./tests/load/run_load_tests.sh
   ./tests/load/run_load_tests.sh
   ```

2. **Run Load Tests with Custom Parameters:**
   You can also run the test with custom parameters:
   ```bash
   ./tests/load/run_load_tests.sh --users 50 --spawn-rate 5 --time 5m --host http://your-api-url
   ```

---

### **Output Files**

- **`load_test_metrics_[timestamp]_stats.csv`**: Contains overall statistics for each endpoint.
  - Includes metrics like response times, request counts, failure rates.
  
- **`load_test_metrics_[timestamp]_stats_history.csv`**: Contains time-series data of the test.
  - Shows how metrics changed over time during the test.
  - Useful for analyzing performance patterns.
  
- **`load_test_metrics_[timestamp]_failures.csv`**: Lists all failed requests.
  - Includes details about what went wrong.
  - Helps in debugging issues.

---

## **Environment Variables (defined in template.yaml)**

- `MONGODB_URI`: MongoDB connection string.
- `FUNCTION_NAME`: AWS Lambda function name.

---


---

## **EXAMPLE CURLS**

Here are a list of curl commands for local testing:

# ProductList - Get all products
curl -X GET 'http://127.0.0.1:3000/api/products'

# ProductGet - Get a specific product
curl -X GET 'http://127.0.0.1:3000/api/products/{id}'

# ProductCreate - Create a new product
curl -X POST 'http://127.0.0.1:3000/api/products' \
  -H 'Content-Type: application/json' \
  -d '{\
    "name": "Example Product",\
    "description": "Product description",\
    "category": "Category",\
    "price": 19.99,\
    "sku": "SKU123"\
  }'

# ProductUpdate - Update a product
curl -X PUT 'http://127.0.0.1:3000/api/products/{id}' \
  -H 'Content-Type: application/json' \
  -d '{\
    "name": "Updated Product",\
    "description": "Updated description",\
    "category": "New Category",\
    "price": 29.99\
  }'

# ProductDelete - Delete a product
curl -X DELETE 'http://127.0.0.1:3000/api/products/{id}'

# InventoryCreate - Create inventory entry
curl -X POST 'http://127.0.0.1:3000/api/inventory' \
  -H 'Content-Type: application/json' \
  -d '{\
    "product_id": "product_id",\
    "store_id": "store_id",\
    "quantity": 100,\
    "minimum_stock": 10\
  }'

# StockInventory - Get store inventory
curl -X GET 'http://127.0.0.1:3000/api/stores/{id}/inventory'

# StockTransfer - Transfer stock between stores
curl -X POST 'http://127.0.0.1:3000/api/inventory/transfer' \
  -H 'Content-Type: application/json' \
  -d '{\
    "product_id": "product_id",\
    "from_store": "store_id_1",\
    "to_store": "store_id_2",\
    "quantity": 50\
  }'

# StockAlerts - Get low stock alerts
curl -X GET 'http://127.0.0.1:3000/api/inventory/alert'

Remember to:

1. Have your MongoDB running (via docker-compose)

2. Have SAM local API running with:

sam local start-api --debug --docker-network inventory-managment-system_backend --log-file ./output.log

3. Replace {id} with actual MongoDB ObjectId values when testing specific products or stores

4. Replace the example JSON payloads with valid data for your system


---

## **DEPLOY TO AWS CLOUD FROM THE LOCAL ENVIRONMENT**

Here are the steps to deploy your application to AWS Cloud:

1. First, build the application:
   ```bash
   sam build
   ```

2. Deploy the application (first time):
   ```bash
   sam deploy --guided
   ```
   This will:
   - Ask for deployment configuration
   - Create a samconfig.toml file with your preferences
   - Prompt for:
     - Stack name
     - AWS Region
     - Confirm changes before deployment
     - Allow SAM CLI IAM role creation
     - Save arguments to samconfig.toml

3. For subsequent deployments:
   ```bash
   sam deploy
   ```

### Important considerations for your application:

1. **MongoDB Connection**:
   - Your current `MONGO_DB_URI` in `template.yaml` points to `mongodb://mongo:27017/`
   - You'll need to change this to a real MongoDB connection string
   - Options:
     - MongoDB Atlas
     - Amazon DocumentDB
     - Self-managed MongoDB on EC2

2. **Environment Variables**:
   In `Globals`:
   ```yaml
   Function:
     Environment:
       Variables:
         MONGO_DB_URI: # Need to update this
         POWERTOOLS_SERVICE_NAME: inventory-management
         LOG_LEVEL: INFO
   ```

3. **Security**:
   - Store sensitive information (like MongoDB URI) in AWS Secrets Manager or Parameter Store
   - Configure VPC settings if using Amazon DocumentDB
   - Set up proper IAM roles and permissions

4. **Monitoring**:
   - CloudWatch Logs will be automatically configured
   - Consider setting up CloudWatch Alarms
   - Lambda Powertools is already integrated for observability

5. **Testing**:
   - Test in a staging environment first
   - Verify MongoDB connectivity
   - Check API Gateway endpoints
   - Test all CRUD operations

After deployment, SAM will output your API Gateway endpoint URL, which you can use to access your API.

For rollback if needed:
```bash
sam delete
```
This will remove all resources created by the stack.

Remember to:
- Keep your MongoDB credentials secure
- Set up proper monitoring and alerts
- Consider implementing API authentication
- Plan for scaling and backup strategies

## **CI/CD IMPLEMENTATION SUGGESTION**

To automate the deployment process and ensure a streamlined release cycle, it is recommended to implement Continuous Integration/Continuous Deployment (CI/CD) for this project.

### **CI/CD Workflow**:

1. **Build and Test**:
   - **Push to GitHub**: Every time code is pushed to the repository (either on a branch or on merge to `main` or `develop`), trigger a CI workflow.
   - **Run Unit Tests**: Use a tool like `pytest` to run unit tests and generate a coverage report.
   - **Run Integration Tests**: Test API endpoints and database integration in a staging environment.

2. **Deployment**:
   - Use **GitHub Actions**, **GitLab CI/CD**, **Jenkins**, or **AWS CodePipeline** to create automated deployment pipelines.
   - Deploy to a **staging** environment first, to allow for testing and validation.
   - If tests pass in staging, automatically deploy to **production**.
   - Ensure the **MONGO_DB_URI** and other environment variables are updated correctly for each environment.

3. **Monitoring and Rollback**:
   - After deployment, set up monitoring with **CloudWatch** and **AWS Lambda Powertools**.
   - In case of failures, automatically roll back to the previous version.

---

## **ANNEXES**

- [Evidence of Integration Tests](docs/evidence_of_integration_tests.txt)
- [Evidence of Load Test](docs/evidence_of_load_test.txt)
- [Evidence of Unit Tests Coverage](docs/evidence_of_unit_tests_coverage.txt)
