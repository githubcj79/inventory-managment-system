# tests/unit/test_movement_service.py
import pytest
from bson import ObjectId
from datetime import datetime
from unittest.mock import Mock

from services.movement_service import MovementService

class TestMovementService:
    @pytest.fixture
    def movement_service(self, mock_db):
        return MovementService(mock_db)

    @pytest.fixture
    def sample_movement_data(self):
        return {
            "productId": str(ObjectId()),
            "type": "IN",
            "quantity": 100,
            "unitPrice": 29.99,
            "date": datetime.utcnow(),
            "reference": "PO-001",
            "notes": "Initial stock"
        }

    def test_create_movement_success(self, movement_service, mock_db, sample_movement_data):
        # Arrange
        mock_db.products.find_one.return_value = {"_id": ObjectId(sample_movement_data["productId"])}
        mock_db.movements.insert_one.return_value.inserted_id = ObjectId()
        mock_db.inventory.find_one.return_value = None
        mock_db.inventory.update_one.return_value.modified_count = 1

        # Act
        result = movement_service.create_movement(sample_movement_data)

        # Assert
        assert result["message"] == "Movement created successfully"
        assert "id" in result
        mock_db.movements.insert_one.assert_called_once()
        mock_db.inventory.update_one.assert_called_once()

    def test_create_movement_invalid_product(self, movement_service, mock_db, sample_movement_data):
        # Arrange
        mock_db.products.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(sample_movement_data)
        assert str(exc.value) == "Product not found"

    def test_create_movement_invalid_product_id_format(self, movement_service, mock_db):
        # Arrange
        invalid_data = {
            "productId": "invalid-id",
            "type": "IN",
            "quantity": 100,
            "date": datetime.utcnow()
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(invalid_data)
        assert str(exc.value) == "Invalid product ID format"

    def test_create_movement_invalid_type(self, movement_service, sample_movement_data):
        # Arrange
        invalid_data = sample_movement_data.copy()
        invalid_data["type"] = "INVALID"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(invalid_data)
        assert str(exc.value) == "Invalid movement type. Must be 'IN' or 'OUT'"

    def test_create_movement_negative_quantity(self, movement_service, sample_movement_data):
        # Arrange
        invalid_data = sample_movement_data.copy()
        invalid_data["quantity"] = -10

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(invalid_data)
        assert str(exc.value) == "Quantity must be positive"

    def test_create_movement_insufficient_stock(self, movement_service, mock_db, sample_movement_data):
        # Arrange
        out_movement = sample_movement_data.copy()
        out_movement["type"] = "OUT"
        mock_db.products.find_one.return_value = {"_id": ObjectId(out_movement["productId"])}
        mock_db.inventory.find_one.return_value = {"quantity": 50}  # Less than requested quantity

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(out_movement)
        assert str(exc.value) == "Insufficient stock"

    def test_create_movement_database_error(self, movement_service, mock_db, sample_movement_data):
        # Arrange
        mock_db.products.find_one.return_value = {"_id": ObjectId(sample_movement_data["productId"])}
        mock_db.movements.insert_one.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(sample_movement_data)
        assert "Error creating movement" in str(exc.value)

    def test_get_movement_by_id_success(self, movement_service, mock_db):
        # Arrange
        movement_id = ObjectId()
        product_id = ObjectId()
        mock_movement = {
            "_id": movement_id,
            "productId": product_id,
            "type": "IN",
            "quantity": 100,
            "date": datetime.utcnow()
        }
        mock_db.movements.find_one.return_value = mock_movement

        # Act
        result = movement_service.get_movement_by_id(str(movement_id))

        # Assert
        assert result["id"] == str(movement_id)
        assert "_id" not in result
        assert isinstance(result["productId"], str)

    def test_get_movement_by_id_not_found(self, movement_service, mock_db):
        # Arrange
        movement_id = str(ObjectId())
        mock_db.movements.find_one.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movement_by_id(movement_id)
        assert str(exc.value) == "Movement not found"

    def test_get_movement_by_id_invalid_id(self, movement_service):
        # Arrange
        invalid_id = "invalid-id"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movement_by_id(invalid_id)
        assert "Invalid movement ID format" in str(exc.value)

    def test_get_movements_by_product_success(self, movement_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_movements = [
            {
                "_id": ObjectId(),
                "productId": ObjectId(product_id),
                "type": "IN",
                "quantity": 100,
                "date": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "productId": ObjectId(product_id),
                "type": "OUT",
                "quantity": 30,
                "date": datetime.utcnow()
            }
        ]
        mock_db.movements.find.return_value = mock_movements

        # Act
        result = movement_service.get_movements_by_product(product_id)

        # Assert
        assert len(result) == 2
        assert all("id" in movement for movement in result)
        assert all("_id" not in movement for movement in result)
        assert all(isinstance(movement["productId"], str) for movement in result)

    def test_get_movements_by_product_invalid_id(self, movement_service):
        # Arrange
        invalid_id = "invalid-id"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movements_by_product(invalid_id)
        assert "Invalid product ID format" in str(exc.value)

    def test_get_movements_by_product_no_movements(self, movement_service, mock_db):
        # Arrange
        product_id = str(ObjectId())
        mock_db.movements.find.return_value = []

        # Act
        result = movement_service.get_movements_by_product(product_id)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_movements_by_date_range(self, movement_service, mock_db):
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        product_id = ObjectId()
        mock_movements = [
            {
                "_id": ObjectId(),
                "productId": product_id,
                "date": datetime(2024, 1, 15),
                "type": "IN",
                "quantity": 100
            },
            {
                "_id": ObjectId(),
                "productId": product_id,
                "date": datetime(2024, 1, 20),
                "type": "OUT",
                "quantity": 50
            }
        ]
        mock_db.movements.find.return_value = mock_movements

        # Act
        result = movement_service.get_movements_by_date_range(start_date, end_date)

        # Assert
        assert len(result) == 2
        assert all("id" in movement for movement in result)
        assert all("_id" not in movement for movement in result)
        assert all(isinstance(movement["productId"], str) for movement in result)

    def test_get_movements_by_date_range_invalid_dates(self, movement_service, mock_db):
        # Arrange
        mock_db.movements.find.side_effect = Exception("Invalid date format")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movements_by_date_range("invalid-date", "invalid-date")
        assert "Error retrieving movements" in str(exc.value)

    def test_get_movements_by_date_range_no_movements(self, movement_service, mock_db):
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        mock_db.movements.find.return_value = []

        # Act
        result = movement_service.get_movements_by_date_range(start_date, end_date)

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_movements_by_type(self, movement_service, mock_db):
        # Arrange
        movement_type = "IN"
        product_id = ObjectId()
        mock_movements = [
            {
                "_id": ObjectId(),
                "productId": product_id,
                "type": "IN",
                "quantity": 100,
                "date": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "productId": product_id,
                "type": "IN",
                "quantity": 50,
                "date": datetime.utcnow()
            }
        ]
        mock_db.movements.find.return_value = mock_movements

        # Act
        result = movement_service.get_movements_by_type(movement_type)

        # Assert
        assert len(result) == 2
        assert all(movement["type"] == "IN" for movement in result)
        assert all("id" in movement for movement in result)
        assert all("_id" not in movement for movement in result)
        assert all(isinstance(movement["productId"], str) for movement in result)

    def test_get_movements_by_type_invalid_type(self, movement_service):
        # Arrange
        invalid_type = "INVALID"

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movements_by_type(invalid_type)
        assert str(exc.value) == "Invalid movement type. Must be 'IN' or 'OUT'"

    def test_get_movements_by_type_no_movements(self, movement_service, mock_db):
        # Arrange
        mock_db.movements.find.return_value = []

        # Act
        result = movement_service.get_movements_by_type("IN")

        # Assert
        assert len(result) == 0
        assert isinstance(result, list)

    def test_get_movements_by_type_database_error(self, movement_service, mock_db):
        # Arrange
        mock_db.movements.find.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.get_movements_by_type("IN")
        assert "Error retrieving movements" in str(exc.value)

    def test_format_movement_missing_id(self, movement_service):
        # Arrange
        movement = {
            "productId": ObjectId(),
            "type": "IN",
            "quantity": 100
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service._format_movement(movement)
        assert "Error formatting movement" in str(exc.value)

    def test_format_movement_with_existing_id(self, movement_service):
        # Arrange
        movement = {
            "id": str(ObjectId()),
            "productId": ObjectId(),
            "type": "IN",
            "quantity": 100
        }

        # Act
        result = movement_service._format_movement(movement)

        # Assert
        assert "id" in result
        assert "_id" not in result
        assert isinstance(result["productId"], str)

    def test_create_movement_missing_required_fields(self, movement_service):
        # Arrange
        invalid_data = {
            "type": "IN",
            "quantity": 100
        }

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(invalid_data)
        assert "productId is required" in str(exc.value)

    def test_create_movement_zero_quantity(self, movement_service, sample_movement_data):
        # Arrange
        invalid_data = sample_movement_data.copy()
        invalid_data["quantity"] = 0

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(invalid_data)
        assert str(exc.value) == "Quantity must be positive"

    def test_create_movement_inventory_update_error(self, movement_service, mock_db, sample_movement_data):
        # Arrange
        mock_db.products.find_one.return_value = {"_id": ObjectId(sample_movement_data["productId"])}
        mock_db.movements.insert_one.return_value.inserted_id = ObjectId()
        mock_db.inventory.update_one.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            movement_service.create_movement(sample_movement_data)
        assert "Error creating movement" in str(exc.value)
