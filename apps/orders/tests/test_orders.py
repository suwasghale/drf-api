from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.product.models import Product, Category
from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem

User = get_user_model()


class OrderIntegrationTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="password123")
        # self.client.login(username="testuser", password="password123") # only works for session auth
        self.client.force_authenticate(user=self.user) # for jwt auth

        # Create a category (required by Product FK)
        self.category = Category.objects.create(name="Electronics")

        # Create sample products
        self.product1 = Product.objects.create(
            name="Product 1", price=100, category = self.category
            )
        self.product2 = Product.objects.create(
            name="Product 2", price=200, category = self.category
            )

        # Create a cart for this user
        self.cart = Cart.objects.create(user=self.user)

    def test_place_order_from_cart(self):
        """Ensure items in cart are moved into an order"""

        # Add items to cart
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

        # Place order
        url = reverse("order-place-order")  # matches @action in OrderViewSet
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)

        order = Order.objects.first()
        self.assertEqual(order.items.count(), 2)  # 2 different products
        self.assertEqual(float(order.total_price), 400.0)  # (2*100 + 1*200)

        # Cart should now be empty
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_place_order_with_empty_cart(self):
        """Should fail if cart is empty"""

        url = reverse("order-place-order")
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cart is empty", response.data["detail"])

# python manage.py test apps/orders/tests/
