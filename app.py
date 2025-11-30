import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

from models import db, Product, AdminSettings


def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///letmemugyou.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from routes.main import main_bp
    from routes.api import api_bp
    from routes.cart import cart_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(admin_bp)

    # Create tables and seed initial data
    with app.app_context():
        db.create_all()
        seed_initial_data()

    return app


def seed_initial_data():
    """Seed initial products if database is empty."""
    if Product.query.first() is None:
        products = [
            Product(
                name='Insulated Tumbler 20oz',
                category='mug',
                base_price=24.99,
                description='20oz stainless steel insulated tumbler. Perfect for hot or cold drinks.',
                image_url='/static/products/tumbler-20oz.svg',
                active=True
            ),
            Product(
                name='Insulated Tumbler 30oz',
                category='mug',
                base_price=29.99,
                description='30oz stainless steel insulated tumbler. Extra capacity for all-day hydration.',
                image_url='/static/products/tumbler-30oz.svg',
                active=True
            ),
            Product(
                name='Insulated Tumbler 40oz',
                category='mug',
                base_price=34.99,
                description='40oz stainless steel insulated tumbler. Maximum capacity for serious hydration.',
                image_url='/static/products/tumbler-40oz.svg',
                active=True
            ),
            Product(
                name='Pint Glass',
                category='glass',
                base_price=14.99,
                description='Classic 16oz pint glass. Great for beer, cocktails, or everyday use.',
                image_url='/static/products/pint-glass.svg',
                active=True
            ),
            Product(
                name='Wine Glass',
                category='glass',
                base_price=16.99,
                description='Elegant stemmed wine glass. Perfect for wine tastings and special occasions.',
                image_url='/static/products/wine-glass.svg',
                active=True
            ),
            Product(
                name='Rocks Glass',
                category='glass',
                base_price=12.99,
                description='Classic rocks/whiskey glass. Ideal for spirits on the rocks.',
                image_url='/static/products/rocks-glass.svg',
                active=True
            ),
            Product(
                name='Round Coaster',
                category='coaster',
                base_price=8.99,
                description='4-inch round stainless steel coaster. Protects surfaces in style.',
                image_url='/static/products/coaster-round.svg',
                active=True
            ),
            Product(
                name='Square Coaster',
                category='coaster',
                base_price=8.99,
                description='4-inch square stainless steel coaster. Modern design for any setting.',
                image_url='/static/products/coaster-square.svg',
                active=True
            ),
            Product(
                name='Keychain',
                category='keychain',
                base_price=6.99,
                description='Stainless steel keychain. Carry your brand everywhere.',
                image_url='/static/products/keychain.svg',
                active=True
            ),
        ]

        # Set sizes for tumblers
        products[0].set_sizes(['20oz'])
        products[1].set_sizes(['30oz'])
        products[2].set_sizes(['40oz'])

        for product in products:
            db.session.add(product)

        # Set default settings
        if AdminSettings.query.first() is None:
            AdminSettings.set('paypal_mode', os.getenv('PAYPAL_MODE', 'sandbox'))
            AdminSettings.set('tax_rate', '0.0825')

        db.session.commit()


# Create app instance
app = create_app()


if __name__ == '__main__':
    app.run(debug=True)
