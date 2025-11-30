from flask import Blueprint, render_template
from models import Product

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with product categories and value proposition."""
    products = Product.query.filter_by(active=True).all()
    categories = {}
    for product in products:
        if product.category not in categories:
            categories[product.category] = []
        categories[product.category].append(product)
    return render_template('index.html', categories=categories)


@main_bp.route('/configurator')
def configurator():
    """Product configurator page."""
    products = Product.query.filter_by(active=True).all()
    return render_template('configurator.html', products=products)
