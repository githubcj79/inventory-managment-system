# tests/unit/test_inventory_service.py
import pytest
from bson import ObjectId
from unittest.mock import Mock

from services.inventory_service import InventoryService

class TestInventoryService:
    @pytest.fixture
    def inventory_service(self, mock_db):
        return InventoryService(mock_db)

    def test_get_product_stock_success(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.find_one.return_value = {
            "productId": ObjectId(product_id),
            "quantity": 100
        }

        # Act
        result = inventory_service.get_product_stock(product_id)

        # Assert
        assert result["productId"] == product_id
        assert result["quantity"] == 100

    def test_get_product_stock_not_found(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.get_product_stock(product_id)
        assert str(exc.value) == "Product not found"

    def test_get_product_stock_no_inventory(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.find_one.return_value = None

        # Act
        result = inventory_service.get_product_stock(product_id)

        # Assert
        assert result["productId"] == product_id
        assert result["quantity"] == 0

    def test_get_product_stock_invalid_id(self, inventory_service):
        # Arrange
        invalid_id = "invalid-id"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.get_product_stock(invalid_id)
        assert "Error retrieving stock" in str(exc.value)

    def test_get_all_stock_success(self, inventory_service, mock_db):
        # Arrange
        mock_inventory = [
            {"productId": ObjectId(), "quantity": 100},
            {"productId": ObjectId(), "quantity": 50}
        ]
        mock_db.inventory.find.return_value = mock_inventory

        # Act
        result = inventory_service.get_all_stock()

        # Assert
        assert len(result) == 2
        assert all(isinstance(item["productId"], str) for item in result)
        assert all(isinstance(item["quantity"], (int, float)) for item in result)

    def test_get_all_stock_empty(self, inventory_service, mock_db):
        # Arrange
        mock_db.inventory.find.return_value = []

        # Act
        result = inventory_service.get_all_stock()

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_all_stock_database_error(self, inventory_service, mock_db):
        # Arrange
        mock_db.inventory.find.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.get_all_stock()
        assert "Error retrieving inventory" in str(exc.value)

    def test_get_low_stock_products_success(self, inventory_service, mock_db):
        # Arrange
        mock_inventory = [
            {"productId": ObjectId(), "quantity": 5},
            {"productId": ObjectId(), "quantity": 8}
        ]
        mock_db.inventory.find.return_value = mock_inventory

        # Act
        result = inventory_service.get_low_stock_products(10)

        # Assert
        assert len(result) == 2
        assert all(item["quantity"] <= 10 for item in result)

    def test_get_low_stock_products_none_found(self, inventory_service, mock_db):
        # Arrange
        mock_db.inventory.find.return_value = []

        # Act
        result = inventory_service.get_low_stock_products(10)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_low_stock_products_database_error(self, inventory_service, mock_db):
        # Arrange
        mock_db.inventory.find.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.get_low_stock_products(10)
        assert "Error retrieving low stock products" in str(exc.value)

    def test_adjust_stock_success(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.update_one.return_value.modified_count = 1

        # Act
        result = inventory_service.adjust_stock(product_id, 100)

        # Assert
        assert result["message"] == "Stock adjusted successfully"
        mock_db.inventory.update_one.assert_called_once()

    def test_adjust_stock_product_not_found(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.adjust_stock(product_id, 100)
        assert str(exc.value) == "Product not found"

    def test_adjust_stock_negative_quantity(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.adjust_stock(product_id, -10)
        assert str(exc.value) == "Quantity must be a positive number"

    def test_adjust_stock_invalid_quantity_type(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.adjust_stock(product_id, "invalid")
        assert str(exc.value) == "Quantity must be a positive number"

    def test_adjust_stock_database_error(self, inventory_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.update_one.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            inventory_service.adjust_stock(product_id, 100)
        assert "Error adjusting stock" in str(exc.value)
