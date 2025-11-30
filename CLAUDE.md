# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

LetMeMugYou is a Flask-based e-commerce platform for custom laser-engraved drinkware (mugs, glasses, coasters, keychains). Customers upload logos, preview them on products using a Fabric.js canvas, and checkout via PayPal.

**Live URL:** https://letmemugyou.com
**Admin:** https://letmemugyou.com/admin

## Technology Stack

- **Backend:** Python 3.12, Flask, SQLAlchemy, SQLite
- **Frontend:** Vanilla JS, Fabric.js (canvas manipulation), CSS (no framework)
- **Payments:** PayPal REST API (sandbox/live toggle in admin)
- **Image Processing:** Pillow (logo to B&W conversion)
- **Production:** Gunicorn + Nginx + systemd

## Project Structure

```
letmemugyou/
├── app.py                 # Main Flask app, config, database seeding
├── models.py              # SQLAlchemy models (Product, Order, OrderItem, AdminSettings)
├── routes/
│   ├── main.py            # Public routes (/, /configurator)
│   ├── api.py             # API endpoints (/api/upload-logo, /api/products)
│   ├── cart.py            # Cart & checkout (/cart, /checkout, PayPal endpoints)
│   └── admin.py           # Admin dashboard (/admin/*)
├── utils/
│   └── email.py           # Email stubs (SMTP ready, needs credentials)
├── static/
│   ├── css/style.css      # All styles
│   ├── js/configurator.js # Fabric.js product configurator
│   ├── products/          # SVG placeholder product images
│   └── uploads/logos/     # Customer uploaded logos (gitignored)
├── templates/
│   ├── base.html          # Base template with nav/footer
│   ├── index.html         # Homepage
│   ├── configurator.html  # Product designer with Fabric.js
│   ├── cart.html          # Shopping cart
│   ├── checkout.html      # Checkout with PayPal buttons
│   ├── order_confirmation.html
│   └── admin/             # Admin templates (6 files)
├── instance/
│   └── letmemugyou.db     # SQLite database (gitignored)
├── .env                   # Environment variables (gitignored)
├── requirements.txt
└── start_gunicorn.sh
```

## Development Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
flask run --debug

# Install dependencies
pip install -r requirements.txt

# Restart production
sudo systemctl restart letmemugyou

# Check logs
sudo journalctl -u letmemugyou -f

# Reload nginx
sudo systemctl reload nginx
```

## Environment Variables (.env)

```
SECRET_KEY=<generated-key>
FLASK_ENV=production
ADMIN_PASSWORD=<admin-password>

# PayPal
PAYPAL_MODE=sandbox  # or 'live'
PAYPAL_SANDBOX_CLIENT_ID=...
PAYPAL_SANDBOX_SECRET=...
PAYPAL_LIVE_CLIENT_ID=...
PAYPAL_LIVE_SECRET=...

# Email (configure when ready)
MAIL_SERVER=box2335.bluehost.com
MAIL_PORT=465
MAIL_USE_SSL=true
MAIL_USERNAME=
MAIL_PASSWORD=
```

## Database Models

| Model | Purpose |
|-------|---------|
| `Product` | id, name, category, base_price, description, image_url, sizes (JSON), active |
| `Order` | Customer info, shipping, totals, status, payment_status, paypal_order_id |
| `OrderItem` | order_id, product_id, size, quantity, logo_filename, logo_position_data (JSON) |
| `AdminSettings` | Key-value store for paypal_mode, tax_rate, admin_email |

## Key Routes

| Route | Purpose |
|-------|---------|
| `/` | Homepage with product categories |
| `/configurator` | Product designer with Fabric.js canvas |
| `/cart` | Shopping cart |
| `/checkout` | Checkout with PayPal integration |
| `/order-confirmation/<order_number>` | Order success page |
| `/api/upload-logo` | POST - Upload and process logo to B&W |
| `/api/products` | GET - List active products |
| `/api/paypal/create-order` | POST - Create PayPal order |
| `/api/paypal/capture-order` | POST - Capture payment, save order |
| `/admin` | Dashboard (requires login) |
| `/admin/orders` | Order management |
| `/admin/products` | Product management |
| `/admin/settings` | PayPal mode toggle, tax rate |

## Fabric.js Configurator

The product configurator (`/configurator`) uses Fabric.js for interactive logo placement:

1. User selects product from dropdown
2. Product SVG loads as canvas background
3. User uploads logo (PNG/JPG/SVG)
4. Logo converted to B&W via `/api/upload-logo` (Pillow)
5. Processed logo added to canvas as draggable/resizable object
6. On "Add to Cart", canvas exports preview as data URL
7. Logo position data (left, top, scaleX, scaleY, angle) saved with cart item

## PayPal Integration

Uses PayPal REST API with Smart Payment Buttons:

1. Frontend renders PayPal button via SDK
2. `createOrder` → `/api/paypal/create-order` → returns PayPal order ID
3. User approves in PayPal popup
4. `onApprove` → `/api/paypal/capture-order` → captures payment, creates DB order
5. Redirect to confirmation page

**Toggle sandbox/live:** Admin → Settings → PayPal Mode

## Nginx Configuration

Located at `/etc/nginx/sites-available/letmemugyou`:
- Proxies to Gunicorn via Unix socket
- Serves `/static/` directly with caching
- HTTPS via Let's Encrypt (run certbot after DNS)

## Systemd Service

Located at `/etc/systemd/system/letmemugyou.service`:
- Runs as `ubuntu:www-data`
- Auto-restarts on failure
- Logs to journald

## Pending Tasks

1. **HTTPS:** Run `sudo certbot --nginx -d letmemugyou.com -d www.letmemugyou.com`
2. **Email:** Configure SMTP credentials in .env for order confirmations
3. **Product Photos:** Replace SVG placeholders with real product images
4. **PayPal Live:** Toggle to "live" in admin when ready for real payments

## Common Issues

| Issue | Solution |
|-------|----------|
| CSS not loading | Check file permissions: `chmod 644 static/css/style.css` |
| 502 Bad Gateway | Check gunicorn: `sudo systemctl status letmemugyou` |
| PayPal errors | Check mode matches credentials (sandbox vs live) |
| Logo upload fails | Check `static/uploads/logos/` permissions |

## Git Repository

- **Remote:** https://github.com/TylerTotally/letmemugyou
- **Ignored:** venv/, .env, instance/, static/uploads/logos/*, __pycache__/
