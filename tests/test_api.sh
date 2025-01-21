#!/bin/bash

# Configuration
API_URL="http://localhost:3000/api"

# Color codes for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Inventory Management System API Testing${NC}"
echo "======================================="

# Helper function to print section headers
print_section() {
    echo -e "\n${GREEN}$1${NC}"
    echo "---------------------------------------"
}

# Helper function to print test results
print_result() {
    echo "Response:"
    echo "$1" | jq '.'
    echo "---------------------------------------"
}

# 1. Test Product Management
print_section "1. Testing Product Management"

# 1.1 List Products (Initial State)
echo "1.1 GET /api/products (Initial state)"
initial_products=$(curl -s -X GET "$API_URL/products")
print_result "$initial_products"

# 1.2 Create Products
print_section "1.2 Creating test products"

# Create first product
echo "Creating Steel Bar product..."
create_response=$(curl -s -X POST "$API_URL/products" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Steel Bar",
        "description": "High-quality steel bar",
        "category": "raw_materials",
        "price": 29.99,
        "sku": "STL001"
    }')
print_result "$create_response"
PRODUCT_ID=$(echo $create_response | jq -r '.id')

# Create second product
echo "Creating Iron Rod product..."
curl -s -X POST "$API_URL/products" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Iron Rod",
        "description": "Standard iron rod",
        "category": "raw_materials",
        "price": 19.99,
        "sku": "IRN002"
    }' | jq '.'

# Create third product
echo "Creating Copper Wire product..."
curl -s -X POST "$API_URL/products" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Copper Wire",
        "description": "Industrial copper wire",
        "category": "raw_materials",
        "price": 39.99,
        "sku": "CPR003"
    }' | jq '.'

# 1.3 List Products (After Creation)
print_section "1.3 GET /api/products (After creation)"
curl -s -X GET "$API_URL/products" | jq '.'

# 1.4 Update Product
print_section "1.4 Testing product update"
echo "Updating Steel Bar product..."
curl -s -X PUT "$API_URL/products/$PRODUCT_ID" \
    -H "Content-Type: application/json" \
    -d '{
        "price": 32.99,
        "description": "Updated high-quality steel bar"
    }' | jq '.'

# 2. Test Inventory Management
print_section "2. Testing Inventory Management"

# 2.1 Create Initial Inventory
echo "2.1 Creating initial inventory for store001..."
curl -s -X POST "$API_URL/inventory" \
    -H "Content-Type: application/json" \
    -d "{
        \"productId\": \"$PRODUCT_ID\",
        \"storeId\": \"store001\",
        \"quantity\": 100,
        \"minStock\": 20
    }" | jq '.'

# 2.2 List Store Inventory
print_section "2.2 Testing store inventory listing"
echo "Checking inventory for store001..."
curl -s -X GET "$API_URL/stores/store001/inventory" | jq '.'

# 3. Test Stock Transfer
print_section "3. Testing Stock Transfer"

# 3.1 Transfer Stock Between Stores
echo "3.1 Transferring stock from store001 to store002..."
curl -s -X POST "$API_URL/inventory/transfer" \
    -H "Content-Type: application/json" \
    -d "{
        \"productId\": \"$PRODUCT_ID\",
        \"sourceStoreId\": \"store001\",
        \"targetStoreId\": \"store002\",
        \"quantity\": 30
    }" | jq '.'

# 3.2 Check Inventory After Transfer
print_section "3.2 Checking inventory levels after transfer"
echo "Source store (store001):"
curl -s -X GET "$API_URL/stores/store001/inventory" | jq '.'
echo "Target store (store002):"
curl -s -X GET "$API_URL/stores/store002/inventory" | jq '.'

# 4. Test Low Stock Alerts
print_section "4. Testing Low Stock Alerts"
echo "Checking for low stock alerts..."
curl -s -X GET "$API_URL/inventory/alert" | jq '.'

# 5. Test Error Cases
print_section "5. Testing Error Cases"

# 5.1 Test duplicate SKU
echo "5.1 Testing duplicate SKU creation..."
curl -s -X POST "$API_URL/products" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Duplicate Steel Bar",
        "description": "This should fail",
        "category": "raw_materials",
        "price": 29.99,
        "sku": "STL001"
    }' | jq '.'

# 5.2 Test invalid transfer (insufficient stock)
echo "5.2 Testing transfer with insufficient stock..."
curl -s -X POST "$API_URL/inventory/transfer" \
    -H "Content-Type: application/json" \
    -d "{
        \"productId\": \"$PRODUCT_ID\",
        \"sourceStoreId\": \"store001\",
        \"targetStoreId\": \"store002\",
        \"quantity\": 1000
    }" | jq '.'

# 5.3 Test invalid product ID
echo "5.3 Testing invalid product ID..."
curl -s -X GET "$API_URL/products/invalid_id" | jq '.'

# 5.4 Test get single product
echo "5.4 Testing get single product..."
curl -s -X GET "$API_URL/products/$PRODUCT_ID" | jq '.'

print_section "API Testing Complete"

# Print summary
echo -e "${GREEN}Tests completed:${NC}"
echo "✓ Product Management (CRUD operations)"
echo "✓ Inventory Management"
echo "✓ Stock Transfers"
echo "✓ Low Stock Alerts"
echo "✓ Error Cases"
