from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # mug, glass, coaster, keychain
    base_price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    sizes = db.Column(db.Text)  # JSON string: ["20oz", "30oz", "40oz"]
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_sizes(self):
        if self.sizes:
            return json.loads(self.sizes)
        return []

    def set_sizes(self, sizes_list):
        self.sizes = json.dumps(sizes_list)


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)

    # Customer info
    customer_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    business_name = db.Column(db.String(100))

    # Shipping address
    address_line1 = db.Column(db.String(200))
    address_line2 = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))

    # Order details
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, shipped
    subtotal = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)

    # Payment
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    paypal_order_id = db.Column(db.String(50))

    # Notes
    notes = db.Column(db.Text)

    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)

    product_name = db.Column(db.String(100))  # Denormalized for history
    size = db.Column(db.String(20))
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float)
    line_total = db.Column(db.Float)

    # Logo info
    logo_filename = db.Column(db.String(255))
    logo_position_data = db.Column(db.Text)  # JSON: {left, top, scaleX, scaleY, angle}
    preview_data_url = db.Column(db.Text)  # Base64 preview image

    product = db.relationship('Product', backref='order_items')

    def get_position_data(self):
        if self.logo_position_data:
            return json.loads(self.logo_position_data)
        return {}

    def set_position_data(self, data):
        self.logo_position_data = json.dumps(data)


class AdminSettings(db.Model):
    __tablename__ = 'admin_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text)

    @staticmethod
    def get(key, default=None):
        setting = AdminSettings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        setting = AdminSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = AdminSettings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
