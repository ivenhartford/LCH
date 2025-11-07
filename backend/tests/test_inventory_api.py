"""
Tests for Inventory Management API endpoints (Vendors, Products, Purchase Orders, Transactions)
"""

import pytest
from app import db
from app.models import User, Vendor, Product, PurchaseOrder, PurchaseOrderItem, InventoryTransaction
from datetime import datetime, date, timedelta
from decimal import Decimal


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client with logged-in user"""
    with client.application.app_context():
        user = User(username="testvet", role="user")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()

    client.post("/api/login", json={"username": "testvet", "password": "password"})
    return client


@pytest.fixture
def admin_client(client):
    """Create authenticated admin client"""
    with client.application.app_context():
        admin = User(username="admin", role="administrator")
        admin.set_password("password")
        db.session.add(admin)
        db.session.commit()

    client.post("/api/login", json={"username": "admin", "password": "password"})
    return client


@pytest.fixture
def sample_vendor(app, authenticated_client):
    """Create a sample vendor for testing"""
    with app.app_context():
        vendor = Vendor(
            company_name="Pet Supplies Inc",
            contact_name="Jane Smith",
            email="jane@petsupplies.com",
            phone="555-1000",
            preferred_vendor=True,
        )
        db.session.add(vendor)
        db.session.commit()
        return vendor.id


@pytest.fixture
def sample_vendors(app, authenticated_client):
    """Create multiple vendors for testing"""
    with app.app_context():
        vendors = [
            Vendor(company_name="Pet Supplies Inc", preferred_vendor=True, is_active=True),
            Vendor(company_name="Medical Distributors", preferred_vendor=False, is_active=True),
            Vendor(company_name="Inactive Vendor", preferred_vendor=False, is_active=False),
        ]
        db.session.add_all(vendors)
        db.session.commit()
        return [v.id for v in vendors]


@pytest.fixture
def sample_product(app, authenticated_client, sample_vendor):
    """Create a sample product for testing"""
    with app.app_context():
        product = Product(
            name="Feline Antibiotic",
            sku="MED-001",
            product_type="medication",
            category="Medications",
            vendor_id=sample_vendor,
            stock_quantity=50,
            reorder_level=10,
            reorder_quantity=30,
            unit_cost=Decimal("5.00"),
            unit_price=Decimal("15.00"),
        )
        db.session.add(product)
        db.session.commit()
        return product.id


@pytest.fixture
def sample_products(app, authenticated_client, sample_vendor):
    """Create multiple products for testing"""
    with app.app_context():
        products = [
            Product(
                name="Product A",
                sku="PROD-A",
                product_type="medication",
                vendor_id=sample_vendor,
                stock_quantity=50,
                reorder_level=10,
                unit_cost=Decimal("5.00"),
                unit_price=Decimal("15.00"),
            ),
            Product(
                name="Product B",
                sku="PROD-B",
                product_type="supply",
                vendor_id=sample_vendor,
                stock_quantity=5,  # Low stock
                reorder_level=10,
                unit_cost=Decimal("2.00"),
                unit_price=Decimal("6.00"),
            ),
            Product(
                name="Inactive Product",
                sku="PROD-INACTIVE",
                product_type="retail",
                vendor_id=sample_vendor,
                stock_quantity=100,
                is_active=False,
            ),
        ]
        db.session.add_all(products)
        db.session.commit()
        return [p.id for p in products]


# ============================================================================
# VENDOR TESTS
# ============================================================================


class TestVendorList:
    def test_get_vendors_empty_list(self, authenticated_client):
        """Should return empty list when no vendors"""
        response = authenticated_client.get("/api/vendors")
        assert response.status_code == 200
        data = response.json
        assert "vendors" in data
        assert isinstance(data["vendors"], list)
        assert len(data["vendors"]) == 0
        assert data["total"] == 0

    def test_get_vendors_with_data(self, authenticated_client, sample_vendors):
        """Should return all vendors"""
        response = authenticated_client.get("/api/vendors")
        assert response.status_code == 200
        data = response.json
        assert "vendors" in data
        assert len(data["vendors"]) == 3
        assert data["total"] == 3

    def test_get_vendors_filter_by_active(self, authenticated_client, sample_vendors):
        """Should filter vendors by active status"""
        response = authenticated_client.get("/api/vendors?is_active=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["vendors"]) == 2  # Only active vendors

    def test_get_vendors_filter_by_preferred(self, authenticated_client, sample_vendors):
        """Should filter vendors by preferred status"""
        response = authenticated_client.get("/api/vendors?preferred=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["vendors"]) == 1
        assert data["vendors"][0]["preferred_vendor"] is True

    def test_get_vendors_search(self, authenticated_client, sample_vendors):
        """Should search vendors by company name"""
        response = authenticated_client.get("/api/vendors?search=Pet")
        assert response.status_code == 200
        data = response.json
        assert len(data["vendors"]) == 1
        assert "Pet" in data["vendors"][0]["company_name"]


class TestVendorDetail:
    def test_get_vendor_by_id(self, authenticated_client, sample_vendor):
        """Should return vendor by ID"""
        response = authenticated_client.get(f"/api/vendors/{sample_vendor}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == sample_vendor
        assert data["company_name"] == "Pet Supplies Inc"

    def test_get_vendor_not_found(self, authenticated_client):
        """Should return 404 for nonexistent vendor"""
        response = authenticated_client.get("/api/vendors/99999")
        assert response.status_code == 404


class TestVendorCreate:
    def test_create_vendor(self, authenticated_client):
        """Should create a new vendor"""
        vendor_data = {
            "company_name": "New Supplier",
            "contact_name": "Bob Jones",
            "email": "bob@newsupplier.com",
            "phone": "555-2000",
            "preferred_vendor": False,
        }
        response = authenticated_client.post("/api/vendors", json=vendor_data)
        assert response.status_code == 201
        data = response.json
        assert data["company_name"] == "New Supplier"
        assert data["email"] == "bob@newsupplier.com"

    def test_create_vendor_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        vendor_data = {}  # Missing required fields
        response = authenticated_client.post("/api/vendors", json=vendor_data)
        assert response.status_code == 400


class TestVendorUpdate:
    def test_update_vendor(self, authenticated_client, sample_vendor):
        """Should update a vendor"""
        update_data = {"email": "newemail@petsupplies.com", "phone": "555-9999"}
        response = authenticated_client.put(f"/api/vendors/{sample_vendor}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["email"] == "newemail@petsupplies.com"
        assert data["phone"] == "555-9999"

    def test_update_vendor_not_found(self, authenticated_client):
        """Should return 404 for nonexistent vendor"""
        response = authenticated_client.put("/api/vendors/99999", json={"email": "test@test.com"})
        assert response.status_code == 404


class TestVendorDelete:
    def test_delete_vendor_soft(self, admin_client, sample_vendor):
        """Should soft delete a vendor"""
        response = admin_client.delete(f"/api/vendors/{sample_vendor}")
        assert response.status_code == 200

        # Verify vendor is deactivated
        with admin_client.application.app_context():
            vendor = Vendor.query.get(sample_vendor)
            assert vendor is not None
            assert vendor.is_active is False

    def test_delete_vendor_hard(self, admin_client, sample_vendor):
        """Should hard delete a vendor"""
        response = admin_client.delete(f"/api/vendors/{sample_vendor}?hard=true")
        assert response.status_code == 200

        # Verify vendor is deleted
        with admin_client.application.app_context():
            vendor = Vendor.query.get(sample_vendor)
            assert vendor is None

    def test_delete_vendor_not_admin(self, authenticated_client, sample_vendor):
        """Should return 403 for non-admin users"""
        response = authenticated_client.delete(f"/api/vendors/{sample_vendor}")
        assert response.status_code == 403


# ============================================================================
# PRODUCT TESTS
# ============================================================================


class TestProductList:
    def test_get_products_empty_list(self, authenticated_client):
        """Should return empty list when no products"""
        response = authenticated_client.get("/api/products")
        assert response.status_code == 200
        data = response.json
        assert "products" in data
        assert len(data["products"]) == 0

    def test_get_products_with_data(self, authenticated_client, sample_products):
        """Should return all products"""
        response = authenticated_client.get("/api/products")
        assert response.status_code == 200
        data = response.json
        assert len(data["products"]) == 3

    def test_get_products_filter_by_active(self, authenticated_client, sample_products):
        """Should filter products by active status"""
        response = authenticated_client.get("/api/products?is_active=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["products"]) == 2

    def test_get_products_filter_by_type(self, authenticated_client, sample_products):
        """Should filter products by type"""
        response = authenticated_client.get("/api/products?product_type=medication")
        assert response.status_code == 200
        data = response.json
        assert len(data["products"]) == 1
        assert data["products"][0]["product_type"] == "medication"

    def test_get_products_low_stock_filter(self, authenticated_client, sample_products):
        """Should filter products by low stock"""
        response = authenticated_client.get("/api/products?low_stock=true")
        assert response.status_code == 200
        data = response.json
        assert len(data["products"]) >= 1
        # Product B should be in low stock (5 <= 10)

    def test_get_products_search(self, authenticated_client, sample_products):
        """Should search products by name or SKU"""
        response = authenticated_client.get("/api/products?search=Product A")
        assert response.status_code == 200
        data = response.json
        assert len(data["products"]) >= 1


class TestProductLowStock:
    def test_get_low_stock_products(self, authenticated_client, sample_products):
        """Should return products that need reordering"""
        response = authenticated_client.get("/api/products/low-stock")
        assert response.status_code == 200
        data = response.json
        assert "products" in data
        # Product B has stock_quantity=5, reorder_level=10
        assert len(data["products"]) >= 1


class TestProductDetail:
    def test_get_product_by_id(self, authenticated_client, sample_product):
        """Should return product by ID"""
        response = authenticated_client.get(f"/api/products/{sample_product}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == sample_product
        assert data["name"] == "Feline Antibiotic"

    def test_get_product_not_found(self, authenticated_client):
        """Should return 404 for nonexistent product"""
        response = authenticated_client.get("/api/products/99999")
        assert response.status_code == 404


class TestProductCreate:
    def test_create_product(self, authenticated_client, sample_vendor):
        """Should create a new product"""
        product_data = {
            "name": "New Product",
            "sku": "NEW-001",
            "product_type": "supply",
            "vendor_id": sample_vendor,
            "stock_quantity": 100,
            "reorder_level": 20,
            "unit_cost": "10.00",
            "unit_price": "25.00",
        }
        response = authenticated_client.post("/api/products", json=product_data)
        assert response.status_code == 201
        data = response.json
        assert data["name"] == "New Product"
        assert data["sku"] == "NEW-001"

    def test_create_product_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        product_data = {"name": "Test"}  # Missing required fields
        response = authenticated_client.post("/api/products", json=product_data)
        assert response.status_code == 400


class TestProductUpdate:
    def test_update_product(self, authenticated_client, sample_product):
        """Should update a product"""
        update_data = {"unit_price": "20.00", "stock_quantity": 75}
        response = authenticated_client.put(f"/api/products/{sample_product}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert float(data["unit_price"]) == 20.00
        assert data["stock_quantity"] == 75

    def test_update_product_not_found(self, authenticated_client):
        """Should return 404 for nonexistent product"""
        response = authenticated_client.put("/api/products/99999", json={"unit_price": "10.00"})
        assert response.status_code == 404


class TestProductDelete:
    def test_delete_product_soft(self, admin_client, sample_product):
        """Should soft delete a product"""
        response = admin_client.delete(f"/api/products/{sample_product}")
        assert response.status_code == 200

        with admin_client.application.app_context():
            product = Product.query.get(sample_product)
            assert product is not None
            assert product.is_active is False

    def test_delete_product_hard(self, admin_client, sample_product):
        """Should hard delete a product"""
        response = admin_client.delete(f"/api/products/{sample_product}?hard=true")
        assert response.status_code == 200

        with admin_client.application.app_context():
            product = Product.query.get(sample_product)
            assert product is None


# ============================================================================
# PURCHASE ORDER TESTS
# ============================================================================


class TestPurchaseOrderList:
    def test_get_purchase_orders_empty_list(self, authenticated_client):
        """Should return empty list when no purchase orders"""
        response = authenticated_client.get("/api/purchase-orders")
        assert response.status_code == 200
        data = response.json
        assert "purchase_orders" in data
        assert len(data["purchase_orders"]) == 0

    def test_get_purchase_orders_with_data(self, authenticated_client, sample_vendor):
        """Should return all purchase orders"""
        # Create a PO
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            po = PurchaseOrder(
                po_number="PO-TEST-001",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()

        response = authenticated_client.get("/api/purchase-orders")
        assert response.status_code == 200
        data = response.json
        assert len(data["purchase_orders"]) == 1

    def test_get_purchase_orders_filter_by_status(self, authenticated_client, sample_vendor):
        """Should filter purchase orders by status"""
        # Create POs with different statuses
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            po1 = PurchaseOrder(
                po_number="PO-001",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="draft",
                created_by_id=user.id,
            )
            po2 = PurchaseOrder(
                po_number="PO-002",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="submitted",
                created_by_id=user.id,
            )
            db.session.add_all([po1, po2])
            db.session.commit()

        response = authenticated_client.get("/api/purchase-orders?status=draft")
        assert response.status_code == 200
        data = response.json
        assert len(data["purchase_orders"]) == 1
        assert data["purchase_orders"][0]["status"] == "draft"


class TestPurchaseOrderDetail:
    def test_get_purchase_order_by_id(self, authenticated_client, sample_vendor):
        """Should return purchase order by ID"""
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            po = PurchaseOrder(
                po_number="PO-DETAIL",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()
            po_id = po.id

        response = authenticated_client.get(f"/api/purchase-orders/{po_id}")
        assert response.status_code == 200
        data = response.json
        assert data["po_number"] == "PO-DETAIL"

    def test_get_purchase_order_not_found(self, authenticated_client):
        """Should return 404 for nonexistent purchase order"""
        response = authenticated_client.get("/api/purchase-orders/99999")
        assert response.status_code == 404


class TestPurchaseOrderCreate:
    def test_create_purchase_order(self, authenticated_client, sample_vendor):
        """Should create a new purchase order with auto-generated PO number"""
        po_data = {
            "vendor_id": sample_vendor,
            "order_date": date.today().isoformat(),
            "status": "draft",
            "subtotal": "0.00",
            "total_amount": "0.00",
        }
        response = authenticated_client.post("/api/purchase-orders", json=po_data)
        assert response.status_code == 201
        data = response.json
        assert "po_number" in data
        assert data["po_number"].startswith("PO-")
        assert data["vendor_id"] == sample_vendor

    def test_create_purchase_order_validation_error(self, authenticated_client):
        """Should return 400 for validation errors"""
        po_data = {}  # Missing required fields
        response = authenticated_client.post("/api/purchase-orders", json=po_data)
        assert response.status_code == 400


class TestPurchaseOrderUpdate:
    def test_update_purchase_order(self, authenticated_client, sample_vendor):
        """Should update a purchase order"""
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            po = PurchaseOrder(
                po_number="PO-UPDATE",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()
            po_id = po.id

        update_data = {"status": "submitted", "notes": "Updated notes"}
        response = authenticated_client.put(f"/api/purchase-orders/{po_id}", json=update_data)
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "submitted"
        assert data["notes"] == "Updated notes"

    def test_update_purchase_order_not_found(self, authenticated_client):
        """Should return 404 for nonexistent purchase order"""
        response = authenticated_client.put(
            "/api/purchase-orders/99999", json={"status": "submitted"}
        )
        assert response.status_code == 404


class TestPurchaseOrderReceive:
    def test_receive_purchase_order(self, authenticated_client, sample_vendor, sample_product):
        """Should mark PO as received and update inventory"""
        # Create PO with items
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            product = Product.query.get(sample_product)
            initial_stock = product.stock_quantity

            po = PurchaseOrder(
                po_number="PO-RECEIVE",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="submitted",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.flush()

            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=sample_product,
                quantity_ordered=20,
                quantity_received=20,
                unit_price=Decimal("5.00"),
            )
            db.session.add(po_item)
            db.session.commit()
            po_id = po.id

        response = authenticated_client.post(f"/api/purchase-orders/{po_id}/receive")
        assert response.status_code == 200
        data = response.json
        assert data["status"] == "received"

        # Verify inventory was updated
        with app.app_context():
            product = Product.query.get(sample_product)
            assert product.stock_quantity == initial_stock + 20

    def test_receive_already_received_po(self, authenticated_client, sample_vendor):
        """Should return 400 for already received PO"""
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            po = PurchaseOrder(
                po_number="PO-ALREADY-RECEIVED",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="received",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()
            po_id = po.id

        response = authenticated_client.post(f"/api/purchase-orders/{po_id}/receive")
        assert response.status_code == 400


class TestPurchaseOrderDelete:
    def test_delete_draft_purchase_order(self, admin_client, sample_vendor):
        """Should delete a draft purchase order"""
        with admin_client.application.app_context():
            user = User.query.filter_by(username="admin").first()
            po = PurchaseOrder(
                po_number="PO-DELETE",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="draft",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()
            po_id = po.id

        response = admin_client.delete(f"/api/purchase-orders/{po_id}")
        assert response.status_code == 200

        with admin_client.application.app_context():
            po = PurchaseOrder.query.get(po_id)
            assert po is None

    def test_delete_non_draft_purchase_order(self, admin_client, sample_vendor):
        """Should not delete a non-draft purchase order"""
        with admin_client.application.app_context():
            user = User.query.filter_by(username="admin").first()
            po = PurchaseOrder(
                po_number="PO-SUBMITTED",
                vendor_id=sample_vendor,
                order_date=date.today(),
                status="submitted",
                created_by_id=user.id,
            )
            db.session.add(po)
            db.session.commit()
            po_id = po.id

        response = admin_client.delete(f"/api/purchase-orders/{po_id}")
        assert response.status_code == 400


# ============================================================================
# INVENTORY TRANSACTION TESTS
# ============================================================================


class TestInventoryTransactionList:
    def test_get_inventory_transactions_empty(self, authenticated_client):
        """Should return empty list when no transactions"""
        response = authenticated_client.get("/api/inventory-transactions")
        assert response.status_code == 200
        data = response.json
        assert "transactions" in data
        assert len(data["transactions"]) == 0

    def test_get_inventory_transactions_with_data(self, authenticated_client, sample_product):
        """Should return inventory transactions"""
        # Create a transaction
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            transaction = InventoryTransaction(
                product_id=sample_product,
                transaction_type="adjustment",
                quantity=10,
                quantity_before=50,
                quantity_after=60,
                reason="Manual adjustment",
                transaction_date=datetime.utcnow(),
                performed_by_id=user.id,
            )
            db.session.add(transaction)
            db.session.commit()

        response = authenticated_client.get("/api/inventory-transactions")
        assert response.status_code == 200
        data = response.json
        assert len(data["transactions"]) >= 1

    def test_get_inventory_transactions_filter_by_product(
        self, authenticated_client, sample_product
    ):
        """Should filter transactions by product"""
        # Create a transaction
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            transaction = InventoryTransaction(
                product_id=sample_product,
                transaction_type="adjustment",
                quantity=10,
                quantity_before=50,
                quantity_after=60,
                transaction_date=datetime.utcnow(),
                performed_by_id=user.id,
            )
            db.session.add(transaction)
            db.session.commit()

        response = authenticated_client.get(
            f"/api/inventory-transactions?product_id={sample_product}"
        )
        assert response.status_code == 200
        data = response.json
        assert len(data["transactions"]) >= 1
        assert data["transactions"][0]["product_id"] == sample_product


class TestInventoryTransactionCreate:
    def test_create_inventory_transaction(self, authenticated_client, sample_product):
        """Should create a manual inventory transaction"""
        transaction_data = {
            "product_id": sample_product,
            "transaction_type": "adjustment",
            "quantity": -5,
            "reason": "Damaged items",
            "transaction_date": datetime.utcnow().isoformat(),
        }
        response = authenticated_client.post("/api/inventory-transactions", json=transaction_data)
        assert response.status_code == 201
        data = response.json
        assert data["product_id"] == sample_product
        assert data["transaction_type"] == "adjustment"
        assert data["quantity"] == -5

        # Verify product stock was updated
        with app.app_context():
            product = Product.query.get(sample_product)
            assert product.stock_quantity == 45  # 50 - 5

    def test_create_inventory_transaction_product_not_found(self, authenticated_client):
        """Should return 404 for nonexistent product"""
        transaction_data = {
            "product_id": 99999,
            "transaction_type": "adjustment",
            "quantity": 10,
            "transaction_date": datetime.utcnow().isoformat(),
        }
        response = authenticated_client.post("/api/inventory-transactions", json=transaction_data)
        assert response.status_code == 404


class TestInventoryTransactionDetail:
    def test_get_inventory_transaction_by_id(self, authenticated_client, sample_product):
        """Should return transaction by ID"""
        with app.app_context():
            user = User.query.filter_by(username="testvet").first()
            transaction = InventoryTransaction(
                product_id=sample_product,
                transaction_type="adjustment",
                quantity=10,
                quantity_before=50,
                quantity_after=60,
                transaction_date=datetime.utcnow(),
                performed_by_id=user.id,
            )
            db.session.add(transaction)
            db.session.commit()
            transaction_id = transaction.id

        response = authenticated_client.get(f"/api/inventory-transactions/{transaction_id}")
        assert response.status_code == 200
        data = response.json
        assert data["id"] == transaction_id

    def test_get_inventory_transaction_not_found(self, authenticated_client):
        """Should return 404 for nonexistent transaction"""
        response = authenticated_client.get("/api/inventory-transactions/99999")
        assert response.status_code == 404
