import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, ImageFilter
import numpy as np
from models import Product, db

api_bp = Blueprint('api', __name__, url_prefix='/api')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_logo_to_bw(image_path, output_path):
    """Convert uploaded image to high-contrast black & white for laser engraving."""
    img = Image.open(image_path)

    # Handle transparency - convert to white background
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        if img.mode in ('RGBA', 'LA'):
            background.paste(img, mask=img.split()[-1])
            img = background
        else:
            img = img.convert('RGB')

    # Convert to grayscale
    img = img.convert('L')

    # Auto contrast for better results
    img = ImageOps.autocontrast(img)

    # Apply threshold for pure B&W
    threshold = 128
    img = img.point(lambda p: 255 if p > threshold else 0)

    # Convert back to RGB for consistency
    img = img.convert('RGB')

    img.save(output_path, 'PNG')
    return img.size  # Return dimensions


def process_logo_transparent(image_path, output_path):
    """Keep the original logo with transparency preserved."""
    img = Image.open(image_path)

    # Convert to RGBA to ensure transparency support
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    img.save(output_path, 'PNG')
    return img.size


def remove_white_background(image_path, output_path, tolerance=30):
    """Remove white/near-white background and make it transparent."""
    img = Image.open(image_path)

    # Convert to RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # Get image data as numpy array
    data = np.array(img)

    # Calculate how "white" each pixel is
    # A pixel is considered white if R, G, B are all above (255 - tolerance)
    r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]

    # Find pixels that are white or near-white
    white_threshold = 255 - tolerance
    white_mask = (r >= white_threshold) & (g >= white_threshold) & (b >= white_threshold)

    # Make white pixels transparent
    data[:, :, 3] = np.where(white_mask, 0, a)

    # Create new image from modified data
    result = Image.fromarray(data, 'RGBA')

    result.save(output_path, 'PNG')
    return result.size


@api_bp.route('/upload-logo', methods=['POST'])
def upload_logo():
    """Handle logo upload, validate, and process based on selected mode."""
    if 'logo' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['logo']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Use PNG, JPG, or SVG.'}), 400

    # Get processing mode: 'bw', 'transparent', or 'remove_bg'
    mode = request.form.get('mode', 'bw')
    if mode not in ('bw', 'transparent', 'remove_bg'):
        mode = 'bw'

    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum 5MB.'}), 400

    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    # Name processed file based on mode
    mode_suffix = {'bw': '_bw', 'transparent': '_trans', 'remove_bg': '_nobg'}
    processed_name = f"{uuid.uuid4().hex}{mode_suffix[mode]}.png"

    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
    os.makedirs(upload_folder, exist_ok=True)

    original_path = os.path.join(upload_folder, unique_name)
    processed_path = os.path.join(upload_folder, processed_name)

    file.save(original_path)

    # Process based on mode (skip processing for SVG)
    if ext != 'svg':
        try:
            if mode == 'bw':
                dimensions = process_logo_to_bw(original_path, processed_path)
            elif mode == 'transparent':
                dimensions = process_logo_transparent(original_path, processed_path)
            elif mode == 'remove_bg':
                dimensions = remove_white_background(original_path, processed_path)
            else:
                dimensions = process_logo_to_bw(original_path, processed_path)
        except Exception as e:
            os.remove(original_path)
            return jsonify({'error': f'Image processing failed: {str(e)}'}), 400
    else:
        # For SVG, just copy
        import shutil
        shutil.copy(original_path, processed_path)
        dimensions = (200, 200)  # Placeholder for SVG

    return jsonify({
        'success': True,
        'original_url': f'/static/uploads/logos/{unique_name}',
        'processed_url': f'/static/uploads/logos/{processed_name}',
        'filename': processed_name,
        'width': dimensions[0],
        'height': dimensions[1],
        'mode': mode
    })


@api_bp.route('/products', methods=['GET'])
def get_products():
    """Get all active products."""
    products = Product.query.filter_by(active=True).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'category': p.category,
        'base_price': p.base_price,
        'description': p.description,
        'image_url': p.image_url,
        'sizes': p.get_sizes()
    } for p in products])


@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get single product details."""
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'category': product.category,
        'base_price': product.base_price,
        'description': product.description,
        'image_url': product.image_url,
        'sizes': product.get_sizes()
    })
