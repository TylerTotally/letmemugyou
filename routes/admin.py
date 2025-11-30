import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import Product, Order, OrderItem, AdminSettings, db
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        flash('Invalid password', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/')
@admin_required
def dashboard():
    """Admin dashboard with stats."""
    # Get stats
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.payment_status == 'paid'
    ).scalar() or 0

    # This month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_orders = Order.query.filter(Order.order_date >= month_start).count()
    monthly_revenue = db.session.query(db.func.sum(Order.total)).filter(
        Order.order_date >= month_start,
        Order.payment_status == 'paid'
    ).scalar() or 0

    pending_orders = Order.query.filter_by(status='pending').count()

    # Recent orders
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()

    # Get PayPal mode
    paypal_mode = AdminSettings.get('paypal_mode', os.getenv('PAYPAL_MODE', 'sandbox'))

    return render_template('admin/dashboard.html',
        total_orders=total_orders,
        total_revenue=total_revenue,
        monthly_orders=monthly_orders,
        monthly_revenue=monthly_revenue,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
        paypal_mode=paypal_mode
    )


@admin_bp.route('/orders')
@admin_required
def orders():
    """Order list with filtering."""
    status = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Order.query

    if status:
        query = query.filter_by(status=status)

    if search:
        query = query.filter(
            db.or_(
                Order.order_number.ilike(f'%{search}%'),
                Order.customer_name.ilike(f'%{search}%'),
                Order.email.ilike(f'%{search}%')
            )
        )

    orders = query.order_by(Order.order_date.desc()).all()
    return render_template('admin/orders.html', orders=orders, status=status, search=search)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Order detail view."""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    """Update order status."""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'processing', 'completed', 'shipped']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}', 'success')
    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/products')
@admin_required
def products():
    """Product management list."""
    products = Product.query.all()
    return render_template('admin/products.html', products=products)


@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    """Add new product."""
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            category=request.form.get('category'),
            base_price=float(request.form.get('base_price', 0)),
            description=request.form.get('description', ''),
            image_url=request.form.get('image_url', ''),
            active=request.form.get('active') == 'on'
        )
        sizes = request.form.get('sizes', '')
        if sizes:
            product.set_sizes([s.strip() for s in sizes.split(',') if s.strip()])
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=None)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    """Edit product."""
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.base_price = float(request.form.get('base_price', 0))
        product.description = request.form.get('description', '')
        product.image_url = request.form.get('image_url', '')
        product.active = request.form.get('active') == 'on'
        sizes = request.form.get('sizes', '')
        if sizes:
            product.set_sizes([s.strip() for s in sizes.split(',') if s.strip()])
        else:
            product.sizes = None
        db.session.commit()
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', product=product)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product(product_id):
    """Delete product."""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted', 'success')
    return redirect(url_for('admin.products'))


@admin_bp.route('/products/<int:product_id>/toggle', methods=['POST'])
@admin_required
def toggle_product(product_id):
    """Toggle product active status."""
    product = Product.query.get_or_404(product_id)
    product.active = not product.active
    db.session.commit()
    return jsonify({'success': True, 'active': product.active})


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings page."""
    if request.method == 'POST':
        # PayPal mode
        paypal_mode = request.form.get('paypal_mode', 'sandbox')
        AdminSettings.set('paypal_mode', paypal_mode)

        # Tax rate
        tax_rate = request.form.get('tax_rate', '0.0825')
        try:
            tax_rate = str(float(tax_rate))
            AdminSettings.set('tax_rate', tax_rate)
        except ValueError:
            flash('Invalid tax rate', 'error')

        # Admin email
        admin_email = request.form.get('admin_email', '')
        AdminSettings.set('admin_email', admin_email)

        flash('Settings saved', 'success')
        return redirect(url_for('admin.settings'))

    # Get current settings
    paypal_mode = AdminSettings.get('paypal_mode', os.getenv('PAYPAL_MODE', 'sandbox'))
    tax_rate = AdminSettings.get('tax_rate', '0.0825')
    admin_email = AdminSettings.get('admin_email', '')

    return render_template('admin/settings.html',
        paypal_mode=paypal_mode,
        tax_rate=tax_rate,
        admin_email=admin_email
    )
