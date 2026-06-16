from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory
from apps.orders.models import Order, OrderStatus
from decimal import Decimal

class AforroAPITests(APITestCase):
    def setUp(self):
        # Setup basic data for tests
        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(title="Laptop Pro", price=Decimal("1200.00"), category=self.category)
        self.product2 = Product.objects.create(title="Laptop Basic", price=Decimal("800.00"), category=self.category)
        
        self.store = Store.objects.create(name="Tech Hub", location="NY")
        
        self.inv1 = Inventory.objects.create(store=self.store, product=self.product1, quantity=10)
        self.inv2 = Inventory.objects.create(store=self.store, product=self.product2, quantity=0)

    def test_order_creation_success_deducts_stock(self):
        """Test #1: Valid order creates a CONFIRMED order and deducts stock."""
        url = reverse('order-create')
        data = {
            "store_id": self.store.id,
            "items": [
                {"product_id": self.product1.id, "quantity_requested": 2}
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], OrderStatus.CONFIRMED)
        
        # Check stock deduction
        self.inv1.refresh_from_db()
        self.assertEqual(self.inv1.quantity, 8)

    def test_order_creation_insufficient_stock_rejected(self):
        """Test #2: Order with insufficient stock creates a REJECTED order without deducting stock."""
        url = reverse('order-create')
        data = {
            "store_id": self.store.id,
            "items": [
                {"product_id": self.product1.id, "quantity_requested": 5},
                {"product_id": self.product2.id, "quantity_requested": 1} # 0 stock
            ]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], OrderStatus.REJECTED)
        
        # Check no stock deduction
        self.inv1.refresh_from_db()
        self.assertEqual(self.inv1.quantity, 10)

    def test_product_search_filter(self):
        """Test #3: Product search filters correctly by title."""
        url = reverse('product-search')
        response = self.client.get(url, {'q': 'Pro'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Laptop Pro")

    def test_autocomplete_prefix_ranking(self):
        """Test #4: Autocomplete ranks prefix matches before general matches."""
        # Create a product where "Laptop" is not at the start
        Product.objects.create(title="Gaming Laptop", price=Decimal("1500.00"), category=self.category)
        
        url = reverse('autocomplete')
        response = self.client.get(url, {'q': 'Lap'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Results should have 'Laptop Pro' and 'Laptop Basic' before 'Gaming Laptop'
        titles = [r['title'] for r in response.data]
        self.assertEqual(len(titles), 3)
        self.assertTrue(titles[0].startswith("Lap"))
        self.assertTrue(titles[1].startswith("Lap"))
        self.assertEqual(titles[2], "Gaming Laptop")
