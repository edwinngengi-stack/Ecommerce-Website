import os
import unittest

os.environ['DATABASE_URL'] = 'sqlite://'

from app import CartItem, Order, OrderItem, Product, User, app, db


class ShopWorkflowTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SECRET_KEY='test-secret')
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            self.user = User(username='shopper', email='shopper@example.com')
            self.user.set_password('secret123')
            self.admin = User(username='admin-test', email='admin@example.com', is_admin=True)
            self.admin.set_password('admin123')
            self.product = Product(
                name='Test product',
                description='A product for workflow tests.',
                price=12.50,
                category='Home',
                stock=5,
            )
            db.session.add_all([self.user, self.admin, self.product])
            db.session.commit()
            self.user_id = self.user.id
            self.admin_id = self.admin.id
            self.product_id = self.product.id
        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self, username, password):
        return self.client.post(
            '/login',
            data={'username': username, 'password': password},
            follow_redirects=True,
        )

    def test_customer_can_place_order_and_stock_is_decremented(self):
        self._login('shopper', 'secret123')
        response = self.client.post(f'/cart/add/{self.product_id}', data={'quantity': 2})
        self.assertEqual(response.status_code, 302)

        response = self.client.post('/checkout', data={'address': '12 Test Street'})
        self.assertEqual(response.status_code, 302)
        with app.app_context():
            product = db.session.get(Product, self.product_id)
            order = Order.query.one()
            self.assertEqual(product.stock, 3)
            self.assertEqual(order.user_id, self.user_id)
            self.assertEqual(order.total, 25.0)
            self.assertEqual(order.items[0].quantity, 2)
            self.assertEqual(CartItem.query.count(), 0)

    def test_checkout_rejects_cart_when_stock_is_no_longer_sufficient(self):
        self._login('shopper', 'secret123')
        self.client.post(f'/cart/add/{self.product_id}', data={'quantity': 2})
        with app.app_context():
            product = db.session.get(Product, self.product_id)
            product.stock = 1
            db.session.commit()

        response = self.client.post(
            '/checkout',
            data={'address': '12 Test Street'},
            follow_redirects=True,
        )
        self.assertIn(b'Insufficient stock', response.data)
        with app.app_context():
            self.assertEqual(Order.query.count(), 0)
            self.assertEqual(CartItem.query.one().quantity, 2)

    def test_customer_can_update_profile_and_password(self):
        self._login('shopper', 'secret123')
        response = self.client.post(
            '/account',
            data={
                'username': 'new-shopper',
                'email': 'new@example.com',
                'current_password': 'secret123',
                'new_password': 'newsecret123',
            },
            follow_redirects=True,
        )
        self.assertIn(b'Your account has been updated.', response.data)
        with app.app_context():
            user = db.session.get(User, self.user_id)
            self.assertEqual(user.username, 'new-shopper')
            self.assertEqual(user.email, 'new@example.com')
            self.assertTrue(user.check_password('newsecret123'))

    def test_admin_can_cancel_order_and_restore_inventory(self):
        with app.app_context():
            product = db.session.get(Product, self.product_id)
            product.stock = 3
            order = Order(
                user_id=self.user_id,
                total=25.0,
                status='confirmed',
                shipping_address='12 Test Street',
            )
            db.session.add(order)
            db.session.flush()
            db.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=self.product_id,
                    quantity=2,
                    price=12.50,
                )
            )
            order_id = order.id
            db.session.commit()

        self._login('admin-test', 'admin123')
        response = self.client.post(
            f'/admin/orders/{order_id}/status',
            data={'status': 'cancelled'},
            follow_redirects=True,
        )
        self.assertIn(b'updated to cancelled', response.data)
        with app.app_context():
            self.assertEqual(db.session.get(Product, self.product_id).stock, 5)
            self.assertEqual(db.session.get(Order, order_id).status, 'cancelled')

    def test_regular_customer_cannot_open_admin_orders(self):
        self._login('shopper', 'secret123')
        response = self.client.get('/admin/orders')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/')


if __name__ == '__main__':
    unittest.main()
