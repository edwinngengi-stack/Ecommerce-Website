from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or os.urandom(32)


def get_database_url():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        return 'sqlite:///' + os.path.join(app.instance_path, 'shop.db')
    if database_url.startswith('postgres://'):
        return database_url.replace('postgres://', 'postgresql+psycopg://', 1)
    if database_url.startswith('postgresql://'):
        return database_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    return database_url


app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', '').lower() == 'true'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(255), default='https://placehold.co/400x400/e8e0d5/5c4a3a?text=Product')
    stock = db.Column(db.Integer, default=10)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    featured = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'category': self.category,
            'image_url': self.image_url,
            'stock': self.stock,
            'featured': self.featured
        }


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    product = db.relationship('Product')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='pending')
    shipping_address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def get_cart_count():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    return 0


@app.context_processor
def inject_globals():
    return {
        'cart_count': get_cart_count(),
        'categories': ['Home', 'Apparel', 'Electronics', 'Wellness', 'Art']
    }


def seed_db():
    admin_username = os.environ.get('ADMIN_USERNAME', '').strip()
    admin_email = os.environ.get('ADMIN_EMAIL', '').strip().lower()
    admin_password = os.environ.get('ADMIN_PASSWORD', '')
    admin_settings = (admin_username, admin_email, admin_password)
    if any(admin_settings) and not all(admin_settings):
        raise RuntimeError('Set ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD together.')
    if admin_password and len(admin_password) < 12:
        raise RuntimeError('ADMIN_PASSWORD must be at least 12 characters.')

    changed = False
    if Product.query.count() == 0:
        products = [
            Product(name='Handwoven Linen Throw', description='Soft, breathable linen throw in warm sand tones. Perfect for cool evenings. Ethically made.', price=68.00, category='Home', image_url='https://images.unsplash.com/photo-1584100936595-c0654b55a2e2?w=400&h=400&fit=crop', stock=15, featured=True),
            Product(name='Ceramic Pour-Over Set', description='Minimalist stoneware pour-over coffee set. Matte finish in soft sage.', price=42.00, category='Home', image_url='https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=400&h=400&fit=crop', stock=22, featured=True),
            Product(name='Organic Cotton Tee', description='Relaxed fit organic cotton t-shirt. Natural undyed color, buttery soft.', price=34.00, category='Apparel', image_url='https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=400&fit=crop', stock=40),
            Product(name='Merino Wool Beanie', description='Lightweight merino wool beanie. Naturally temperature regulating.', price=28.00, category='Apparel', image_url='https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=400&h=400&fit=crop', stock=30, featured=True),
            Product(name='Portable Bluetooth Speaker', description='Compact speaker with warm, clear sound. 12-hour battery. Soft-touch silicone.', price=79.00, category='Electronics', image_url='https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=400&fit=crop', stock=18),
            Product(name='Noise-Canceling Earbuds', description='Comfortable in-ear buds with adaptive noise canceling and 8-hour playtime.', price=129.00, category='Electronics', image_url='https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400&h=400&fit=crop', stock=12, featured=True),
            Product(name='Lavender Sleep Mist', description='Calming room and linen spray with pure lavender and cedar. 100ml.', price=24.00, category='Wellness', image_url='https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=400&h=400&fit=crop', stock=35),
            Product(name='Bamboo Yoga Mat', description='Natural rubber and bamboo fiber mat. Extra cushioning, non-slip.', price=58.00, category='Wellness', image_url='https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=400&h=400&fit=crop', stock=20),
            Product(name='Abstract Line Print', description='Limited edition giclée print on archival paper. Soft charcoal lines on cream.', price=45.00, category='Art', image_url='https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=400&h=400&fit=crop', stock=8, featured=True),
            Product(name='Handmade Ceramic Vase', description='Wheel-thrown stoneware vase with reactive glaze. Each piece unique.', price=52.00, category='Art', image_url='https://images.unsplash.com/photo-1578500494198-246f612d3b3d?w=400&h=400&fit=crop', stock=10),
            Product(name='Linen Crossbody Bag', description='Lightweight linen bag with leather strap. Perfect everyday size.', price=64.00, category='Apparel', image_url='https://images.unsplash.com/photo-1590874103328-eac38a67437f?w=400&h=400&fit=crop', stock=14),
            Product(name='Smart Desk Lamp', description='Adjustable color temperature LED lamp with wireless charging base.', price=89.00, category='Electronics', image_url='https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop', stock=16),
        ]
        for p in products:
            db.session.add(p)
        changed = True

    if admin_username:
        matching_users = User.query.filter(
            (User.username == admin_username) | (User.email == admin_email)
        ).all()
        if matching_users:
            existing_admin = matching_users[0]
            if (
                len(matching_users) != 1
                or not existing_admin.is_admin
                or existing_admin.username != admin_username
                or existing_admin.email != admin_email
            ):
                raise RuntimeError('Configured admin username or email is already in use.')
        else:
            admin = User(username=admin_username, email=admin_email, is_admin=True)
            admin.set_password(admin_password)
            db.session.add(admin)
            changed = True

    if changed:
        db.session.commit()
        print('Database initialized.')


@app.route('/')
def index():
    featured = Product.query.filter_by(featured=True).limit(4).all()
    products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    return render_template('index.html', featured=featured, products=products)


@app.route('/products')
def products():
    category = request.args.get('category')
    search = request.args.get('q', '').strip()
    query = Product.query
    if category:
        query = query.filter_by(category=category)
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))
    products = query.order_by(Product.name).all()
    return render_template('products.html', products=products, current_category=category, search=search)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related = Product.query.filter(Product.category == product.category, Product.id != product.id).limit(4).all()
    return render_template('product_detail.html', product=product, related=related)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Account created successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page or url_for('index'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')

        if not username or not email:
            flash('Username and email are required.', 'error')
            return render_template('account.html')
        if User.query.filter(
            User.id != current_user.id,
            (User.username == username) | (User.email == email)
        ).first():
            flash('That username or email is already in use.', 'error')
            return render_template('account.html')
        if new_password:
            if not current_user.check_password(current_password):
                flash('Enter your current password to change it.', 'error')
                return render_template('account.html')
            if len(new_password) < 6:
                flash('Your new password must be at least 6 characters.', 'error')
                return render_template('account.html')
            current_user.set_password(new_password)

        current_user.username = username
        current_user.email = email
        db.session.commit()
        flash('Your account has been updated.', 'success')
        return redirect(url_for('account'))
    return render_template('account.html')


@app.route('/cart')
@login_required
def cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in items)
    return render_template('cart.html', items=items, total=total)


@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Enter a valid quantity.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    if quantity < 1:
        flash('Quantity must be at least 1.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    cart_quantity = item.quantity if item else 0
    if product.stock < cart_quantity + quantity:
        flash('Not enough stock available.', 'error')
        return redirect(url_for('product_detail', product_id=product_id))
    if item:
        item.quantity += quantity
    else:
        item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(item)
    db.session.commit()
    flash(f'{product.name} added to cart.', 'success')
    return redirect(request.referrer or url_for('cart'))


@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    try:
        quantity = int(request.form.get('quantity', 1))
    except ValueError:
        flash('Enter a valid quantity.', 'error')
        return redirect(url_for('cart'))
    if quantity <= 0:
        db.session.delete(item)
    elif quantity > item.product.stock:
        flash(f'Only {item.product.stock} units of {item.product.name} are in stock.', 'error')
        return redirect(url_for('cart'))
    else:
        item.quantity = quantity
    db.session.commit()
    return redirect(url_for('cart'))


@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash('Your cart is empty.', 'info')
        return redirect(url_for('products'))
    total = sum(item.product.price * item.quantity for item in items)
    if request.method == 'POST':
        address = request.form.get('address', '').strip()
        if not address:
            flash('Shipping address is required.', 'error')
            return render_template('checkout.html', items=items, total=total)
        unavailable = [
            item for item in items
            if item.quantity > item.product.stock
        ]
        if unavailable:
            names = ', '.join(item.product.name for item in unavailable)
            flash(f'Insufficient stock for: {names}. Update your cart and try again.', 'error')
            return redirect(url_for('cart'))
        order = Order(user_id=current_user.id, total=total, shipping_address=address, status='confirmed')
        db.session.add(order)
        db.session.flush()
        for item in items:
            order_item = OrderItem(order_id=order.id, product_id=item.product_id,
                                   quantity=item.quantity, price=item.product.price)
            db.session.add(order_item)
            item.product.stock -= item.quantity
            db.session.delete(item)
        db.session.commit()
        flash(f'Order #{order.id} placed successfully.', 'success')
        return redirect(url_for('orders'))
    return render_template('checkout.html', items=items, total=total)


@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)


@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
    return render_template('order_detail.html', order=order)


@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin_orders.html', orders=orders, order_statuses=ORDER_STATUSES)


ORDER_STATUSES = ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')


@app.route('/admin/orders/<int:order_id>/status', methods=['POST'])
@login_required
def admin_update_order_status(order_id):
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '')
    if new_status not in ORDER_STATUSES:
        flash('Select a valid order status.', 'error')
        return redirect(url_for('admin_orders'))
    if order.status == 'cancelled' and new_status != 'cancelled':
        flash('Cancelled orders cannot be reopened.', 'error')
        return redirect(url_for('admin_orders'))
    if new_status == 'cancelled' and order.status != 'cancelled':
        if order.status in ('shipped', 'delivered'):
            flash('Orders that have shipped cannot be cancelled here.', 'error')
            return redirect(url_for('admin_orders'))
        for item in order.items:
            item.product.stock += item.quantity
    order.status = new_status
    db.session.commit()
    flash(f'Order #{order.id} updated to {new_status}.', 'success')
    return redirect(url_for('admin_orders'))


@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    products = Product.query.order_by(Product.name).all()
    return render_template('admin_products.html', products=products)


@app.route('/admin/products/new', methods=['GET', 'POST'])
@login_required
def admin_new_product():
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=float(request.form.get('price', 0)),
            category=request.form.get('category'),
            stock=int(request.form.get('stock', 0)),
            image_url=request.form.get('image_url') or 'https://placehold.co/400x400/e8e0d5/5c4a3a?text=Product',
            featured=bool(request.form.get('featured'))
        )
        db.session.add(product)
        db.session.commit()
        flash('Product created.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin_product_form.html', product=None)


@app.route('/admin/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price', 0))
        product.category = request.form.get('category')
        product.stock = int(request.form.get('stock', 0))
        product.image_url = request.form.get('image_url') or product.image_url
        product.featured = bool(request.form.get('featured'))
        db.session.commit()
        flash('Product updated.', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin_product_form.html', product=product)


@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))


@app.route('/api/products', methods=['GET'])
def api_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])


@app.route('/api/products/<int:product_id>', methods=['GET'])
def api_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())


@app.route('/api/products', methods=['POST'])
@login_required
def api_create_product():
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json() or {}
    product = Product(
        name=data.get('name'),
        description=data.get('description', ''),
        price=float(data.get('price', 0)),
        category=data.get('category', 'Home'),
        stock=int(data.get('stock', 0)),
        image_url=data.get('image_url', 'https://placehold.co/400x400/e8e0d5/5c4a3a?text=Product'),
        featured=bool(data.get('featured', False))
    )
    db.session.add(product)
    db.session.commit()
    return jsonify(product.to_dict()), 201


@app.route('/api/products/<int:product_id>', methods=['PUT'])
@login_required
def api_update_product(product_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = float(data.get('price', product.price))
    product.category = data.get('category', product.category)
    product.stock = int(data.get('stock', product.stock))
    product.image_url = data.get('image_url', product.image_url)
    product.featured = bool(data.get('featured', product.featured))
    db.session.commit()
    return jsonify(product.to_dict())


@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@login_required
def api_delete_product(product_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200


@app.route('/api/cart', methods=['GET'])
@login_required
def api_cart():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': i.id,
        'product': i.product.to_dict(),
        'quantity': i.quantity,
        'subtotal': i.product.price * i.quantity
    } for i in items])


with app.app_context():
    os.makedirs(app.instance_path, exist_ok=True)
    db.create_all()
    seed_db()


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host=os.environ.get('HOST', '127.0.0.1'), port=5000)
