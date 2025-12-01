# LetMeMugYou

A Flask-based e-commerce platform for custom laser-engraved drinkware. Customers can upload their logos, preview them on products using an interactive canvas, and checkout via PayPal.

**Live Site:** https://letmemugyou.com

## Features

- **Interactive Product Configurator** - Drag, resize, and rotate logos on products using Fabric.js
- **Logo Processing Options**
  - Black & White conversion (optimized for laser engraving)
  - Keep Original (preserve colors & transparency)
  - Remove White Background (make white areas transparent)
- **Product Categories** - Mugs, glasses, coasters, keychains
- **Shopping Cart** - Session-based cart with preview images
- **PayPal Integration** - Sandbox and live mode support
- **Admin Dashboard** - Manage orders, products, and settings

## Tech Stack

- **Backend:** Python 3.12, Flask, SQLAlchemy, SQLite
- **Frontend:** Vanilla JavaScript, Fabric.js, CSS
- **Payments:** PayPal REST API
- **Image Processing:** Pillow, NumPy
- **Production:** Gunicorn + Nginx + systemd

## Quick Start

```bash
# Clone the repository
git clone https://github.com/TylerTotally/letmemugyou.git
cd letmemugyou

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run development server
flask run --debug
```

## Environment Variables

Create a `.env` file with:

```
SECRET_KEY=your-secret-key
FLASK_ENV=development
ADMIN_PASSWORD=your-admin-password

# PayPal
PAYPAL_MODE=sandbox
PAYPAL_SANDBOX_CLIENT_ID=your-sandbox-client-id
PAYPAL_SANDBOX_SECRET=your-sandbox-secret
PAYPAL_LIVE_CLIENT_ID=your-live-client-id
PAYPAL_LIVE_SECRET=your-live-secret
```

## Project Structure

```
letmemugyou/
├── app.py                 # Flask app & config
├── models.py              # Database models
├── routes/
│   ├── main.py            # Public routes
│   ├── api.py             # API endpoints
│   ├── cart.py            # Cart & checkout
│   └── admin.py           # Admin dashboard
├── static/
│   ├── css/style.css
│   ├── js/configurator.js # Fabric.js canvas
│   └── uploads/logos/     # Customer uploads
└── templates/             # Jinja2 templates
```

## License

MIT
