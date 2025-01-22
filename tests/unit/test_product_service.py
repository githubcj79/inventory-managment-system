import pytest
from bson import ObjectId
from unittest.mock import Mock

from services.product_service import ProductService

class TestProductService:
    @pytest.fixture
    def product_service(self, mock_db):
        return ProductService(mock_db)

    @pytest.fixture
    def sample_product_data(self):
        return {
            "name": "Steel Bar",
            "description": "High-quality steel bar",
            "category": "raw_materials",
            "price": 29.99,
            "sku": "STL001"
        }

    def test_create_product_success(self, product_service, mock_db, sample_product_data):
        # Arrange
        mock_db.products.find_one.return_value = None
        mock_db.products.insert_one.return_value.inserted_id = ObjectId()

        # Act
        result = product_service.create_product(sample_product_data)

        # Assert
        assert result["message"] == "Product created successfully"
        assert "id" in result
        mock_db.products.insert_one.assert_called_once_with(sample_product_data)

    def test_create_product_duplicate_sku(self, product_service, mock_db, sample_product_data):
        # Arrange
        mock_db.products.find_one.return_value = {"_id": ObjectId()}

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.create_product(sample_product_data)
        assert str(exc.value) == "SKU already exists"

    def test_create_product_missing_field(self, product_service):
        # Arrange
        incomplete_data = {
            "name": "Steel Bar",
            "description": "High-quality steel bar"
            # missing required fields
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.create_product(incomplete_data)
        assert "Missing required field:" in str(exc.value)

    def test_get_product_by_id_success(self, product_service, mock_db):
        # Arrange
        product_id = ObjectId()
        mock_product = {
            "_id": product_id,
            "name": "Steel Bar",
            "description": "High-quality steel bar",
            "category": "raw_materials",
            "price": 29.99,
            "sku": "STL001"
        }
        mock_db.products.find_one.return_value = mock_product

        # Act
        result = product_service.get_product_by_id(str(product_id))

        # Assert
        assert result["id"] == str(product_id)
        assert "name" in result
        assert "_id" not in result

    def test_get_product_by_id_not_found(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.get_product_by_id(product_id)
        assert str(exc.value) == "Product not found"

    def test_get_product_by_id_invalid_object_id(self, product_service):
        # Arrange
        invalid_id = "invalid-object-id"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.get_product_by_id(invalid_id)
        assert "Invalid product ID" in str(exc.value)

    def test_update_product_success(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        update_data = {"name": "Updated Steel Bar"}
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.products.update_one.return_value.modified_count = 1

        # Act
        result = product_service.update_product(product_id, update_data)

        # Assert
        assert result["message"] == "Product updated successfully"
        mock_db.products.update_one.assert_called_once()

    def test_update_product_not_found(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        update_data = {"name": "New Name"}
        mock_db.products.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.update_product(product_id, update_data)
        assert str(exc.value) == "Product not found"

    def test_update_product_invalid_object_id(self, product_service):
        # Arrange
        invalid_id = "invalid-object-id"
        update_data = {"name": "New Name"}

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.update_product(invalid_id, update_data)
        assert "Invalid product ID" in str(exc.value)

    def test_update_product_no_changes(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        update_data = {"name": "New Name"}
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.products.update_one.return_value.modified_count = 0

        # Act
        result = product_service.update_product(product_id, update_data)

        # Assert
        assert result["message"] == "No changes made to product"

    def test_update_product_duplicate_sku(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        update_data = {"sku": "EXISTING-SKU"}
        mock_db.products.find_one.side_effect = [
            {"_id": ObjectId(product_id)},  # First call: product exists
            {"_id": ObjectId()}  # Second call: existing SKU found
        ]

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.update_product(product_id, update_data)
        assert str(exc.value) == "SKU already exists"

    def test_delete_product_success(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.find_one.return_value = None
        mock_db.products.delete_one.return_value.deleted_count = 1

        # Act
        result = product_service.delete_product(product_id)

        # Assert
        assert result["message"] == "Product deleted successfully"
        mock_db.products.delete_one.assert_called_once()

    def test_delete_product_in_inventory(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.find_one.return_value = {"_id": ObjectId()}

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.delete_product(product_id)
        assert str(exc.value) == "Cannot delete product that exists in inventory"

    def test_delete_product_invalid_object_id(self, product_service):
        # Arrange
        invalid_id = "invalid-object-id"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            product_service.delete_product(invalid_id)
        assert "Invalid product ID" in str(exc.value)

    def test_delete_product_not_found_after_check(self, product_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.products.find_one.return_value = {"_id": ObjectId(product_id)}
        mock_db.inventory.find_one.return_value = None
        mock_db.products.delete_one.return_value.deleted_count = 0

        # Act
        result = product_service.delete_product(product_id)

        # Assert
        assert result["message"] == "Product not found"

    def test_get_all_products(self, product_service, mock_db):
        # Arrange
        mock_products = [
            {"_id": ObjectId(), "name": "Product 1"},
            {"_id": ObjectId(), "name": "Product 2"}
        ]
        mock_db.products.find.return_value.skip.return_value.limit.return_value = mock_products

        # Act
        result = product_service.get_all_products(skip=0, limit=10)

        # Assert
        assert len(result) == 2
        assert all("id" in product for product in result)
        assert all("_id" not in product for product in result)

    def test_search_products(self, product_service, mock_db):
        # Arrange
        mock_products = [
            {"_id": ObjectId(), "name": "Steel Bar", "sku": "STL001"},
            {"_id": ObjectId(), "name": "Steel Rod", "sku": "STL002"}
        ]
        mock_db.products.find.return_value = mock_products

        # Act
        result = product_service.search_products("Steel")

        # Assert
        assert len(result) == 2
        assert all("id" in product for product in result)
        assert all("Steel" in product["name"] for product in result)
