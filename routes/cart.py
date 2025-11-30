import os
import uuid
import requests
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from models import Product, Order, OrderItem, AdminSettings, db

cart_bp = Blueprint('cart', __name__)


def get_cart():
    """Get cart from session."""
    if 'cart' not in session:
        session['cart'] = []
    return session['cart']


def save_cart(cart):
    """Save cart to session."""
    session['cart'] = cart
    session.modified = True


def calculate_totals(cart):
    """Calculate cart totals."""
    subtotal = sum(item['line_total'] for item in cart)
    tax_rate = float(AdminSettings.get('tax_rate', '0.0825'))  # Default 8.25%
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)
    return {'subtotal': subtotal, 'tax': tax, 'total': total, 'tax_rate': tax_rate}


@cart_bp.route('/cart')
def view_cart():
    """View shopping cart."""
    cart = get_cart()
    totals = calculate_totals(cart)
    return render_template('cart.html', cart=cart, totals=totals)


@cart_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add item to cart."""
    data = request.json
    product_id = data.get('product_id')
    size = data.get('size')
    quantity = int(data.get('quantity', 1))
    logo_filename = data.get('logo_filename')
    logo_position = data.get('logo_position', {})
    preview_data_url = data.get('preview_data_url')

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    cart = get_cart()

    cart_item = {
        'id': str(uuid.uuid4()),
        'product_id': product.id,
        'product_name': product.name,
        'category': product.category,
        'size': size,
        'quantity': quantity,
        'unit_price': product.base_price,
        'line_total': round(product.base_price * quantity, 2),
        'logo_filename': logo_filename,
        'logo_position': logo_position,
        'preview_data_url': preview_data_url,
        'image_url': product.image_url
    }

    cart.append(cart_item)
    save_cart(cart)

    return jsonify({'success': True, 'cart_count': len(cart)})


@cart_bp.route('/cart/update', methods=['POST'])
def update_cart():
    """Update cart item quantity."""
    data = request.json
    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    cart = get_cart()
    for item in cart:
        if item['id'] == item_id:
            item['quantity'] = quantity
            item['line_total'] = round(item['unit_price'] * quantity, 2)
            break

    save_cart(cart)
    totals = calculate_totals(cart)
    return jsonify({'success': True, 'totals': totals})


@cart_bp.route('/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove item from cart."""
    data = request.json
    item_id = data.get('item_id')

    cart = get_cart()
    cart = [item for item in cart if item['id'] != item_id]
    save_cart(cart)

    totals = calculate_totals(cart)
    return jsonify({'success': True, 'cart_count': len(cart), 'totals': totals})


@cart_bp.route('/checkout')
def checkout():
    """Checkout page."""
    cart = get_cart()
    if not cart:
        return redirect(url_for('cart.view_cart'))
    totals = calculate_totals(cart)

    # Get PayPal mode from settings
    paypal_mode = AdminSettings.get('paypal_mode', os.getenv('PAYPAL_MODE', 'sandbox'))
    if paypal_mode == 'live':
        paypal_client_id = os.getenv('PAYPAL_LIVE_CLIENT_ID')
    else:
        paypal_client_id = os.getenv('PAYPAL_SANDBOX_CLIENT_ID')

    return render_template('checkout.html', cart=cart, totals=totals, paypal_client_id=paypal_client_id)


def get_paypal_access_token():
    """Get PayPal access token."""
    paypal_mode = AdminSettings.get('paypal_mode', os.getenv('PAYPAL_MODE', 'sandbox'))

    if paypal_mode == 'live':
        api_base = 'https://api-m.paypal.com'
        client_id = os.getenv('PAYPAL_LIVE_CLIENT_ID')
        secret = os.getenv('PAYPAL_LIVE_SECRET')
    else:
        api_base = 'https://api-m.sandbox.paypal.com'
        client_id = os.getenv('PAYPAL_SANDBOX_CLIENT_ID')
        secret = os.getenv('PAYPAL_SANDBOX_SECRET')

    response = requests.post(
        f'{api_base}/v1/oauth2/token',
        headers={'Accept': 'application/json'},
        data={'grant_type': 'client_credentials'},
        auth=(client_id, secret)
    )
    response.raise_for_status()
    return response.json()['access_token'], api_base


def generate_order_number():
    """Generate unique order number."""
    import random
    import string
    prefix = 'LMM'
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f'{prefix}-{suffix}'


@cart_bp.route('/api/paypal/create-order', methods=['POST'])
def create_paypal_order():
    """Create PayPal order."""
    cart = get_cart()
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    totals = calculate_totals(cart)

    try:
        access_token, api_base = get_paypal_access_token()

        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': 'USD',
                    'value': f"{totals['total']:.2f}",
                    'breakdown': {
                        'item_total': {'currency_code': 'USD', 'value': f"{totals['subtotal']:.2f}"},
                        'tax_total': {'currency_code': 'USD', 'value': f"{totals['tax']:.2f}"}
                    }
                }
            }],
            'application_context': {
                'brand_name': 'Let Me Mug You',
                'user_action': 'PAY_NOW'
            }
        }

        response = requests.post(
            f'{api_base}/v2/checkout/orders',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            },
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return jsonify({'orderID': data['id']})

    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f'PayPal create order error: {e.response.text}')
        return jsonify({'error': 'Payment service error'}), 500
    except Exception as e:
        current_app.logger.error(f'PayPal error: {str(e)}')
        return jsonify({'error': 'Payment service error'}), 500


@cart_bp.route('/api/paypal/capture-order', methods=['POST'])
def capture_paypal_order():
    """Capture PayPal order and create order in database."""
    data = request.json
    paypal_order_id = data.get('orderID')
    customer_info = data.get('customer', {})

    cart = get_cart()
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400

    try:
        access_token, api_base = get_paypal_access_token()

        # Capture the payment
        response = requests.post(
            f'{api_base}/v2/checkout/orders/{paypal_order_id}/capture',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}'
            }
        )
        response.raise_for_status()
        capture_data = response.json()

        if capture_data['status'] != 'COMPLETED':
            return jsonify({'error': 'Payment not completed'}), 400

        # Create order in database
        totals = calculate_totals(cart)
        order = Order(
            order_number=generate_order_number(),
            customer_name=customer_info.get('name', ''),
            email=customer_info.get('email', ''),
            phone=customer_info.get('phone', ''),
            business_name=customer_info.get('business_name', ''),
            address_line1=customer_info.get('address_line1', ''),
            address_line2=customer_info.get('address_line2', ''),
            city=customer_info.get('city', ''),
            state=customer_info.get('state', ''),
            zip_code=customer_info.get('zip_code', ''),
            subtotal=totals['subtotal'],
            tax=totals['tax'],
            total=totals['total'],
            payment_status='paid',
            paypal_order_id=paypal_order_id,
            notes=customer_info.get('notes', '')
        )
        db.session.add(order)
        db.session.flush()  # Get order ID

        # Create order items
        for item in cart:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product_id'],
                product_name=item['product_name'],
                size=item.get('size', ''),
                quantity=item['quantity'],
                unit_price=item['unit_price'],
                line_total=item['line_total'],
                logo_filename=item.get('logo_filename', ''),
                preview_data_url=item.get('preview_data_url', '')
            )
            order_item.set_position_data(item.get('logo_position', {}))
            db.session.add(order_item)

        db.session.commit()

        # Clear cart
        session.pop('cart', None)

        # TODO: Send confirmation emails

        return jsonify({
            'success': True,
            'order_number': order.order_number,
            'redirect': url_for('cart.order_confirmation', order_number=order.order_number)
        })

    except requests.exceptions.HTTPError as e:
        current_app.logger.error(f'PayPal capture error: {e.response.text}')
        db.session.rollback()
        return jsonify({'error': 'Payment capture failed'}), 500
    except Exception as e:
        current_app.logger.error(f'Order creation error: {str(e)}')
        db.session.rollback()
        return jsonify({'error': 'Order creation failed'}), 500


@cart_bp.route('/order-confirmation/<order_number>')
def order_confirmation(order_number):
    """Order confirmation page."""
    order = Order.query.filter_by(order_number=order_number).first_or_404()
    return render_template('order_confirmation.html', order=order)
