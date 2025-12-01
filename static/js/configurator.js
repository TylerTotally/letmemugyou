// Configurator with Fabric.js
let canvas;
let productImage = null;
let logoImage = null;
let currentProduct = null;
let uploadedLogoUrl = null;
let uploadedLogoFilename = null;
let originalLogoFile = null;  // Store original file for reprocessing

// Initialize canvas
document.addEventListener('DOMContentLoaded', function() {
    canvas = new fabric.Canvas('preview-canvas', {
        backgroundColor: '#f5f5f5',
        selection: true
    });

    // Set up file upload
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('logo-upload');

    uploadZone.addEventListener('click', () => fileInput.click());

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Set up logo mode change handlers - reprocess when mode changes
    const modeRadios = document.querySelectorAll('input[name="logo-mode"]');
    modeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (originalLogoFile) {
                handleFileUpload(originalLogoFile);
            }
        });
    });

    // Check for category in URL
    const urlParams = new URLSearchParams(window.location.search);
    const category = urlParams.get('category');
    if (category) {
        filterProductsByCategory(category);
    }
});

function filterProductsByCategory(category) {
    const select = document.getElementById('product-select');
    const options = select.querySelectorAll('option');
    // This would filter options - for now just show all
}

function updateProduct() {
    const select = document.getElementById('product-select');
    const option = select.options[select.selectedIndex];

    if (!option.value) {
        currentProduct = null;
        canvas.clear();
        canvas.backgroundColor = '#f5f5f5';
        canvas.renderAll();
        updatePrice();
        checkAddToCart();
        return;
    }

    currentProduct = {
        id: parseInt(option.value),
        price: parseFloat(option.dataset.price),
        imageUrl: option.dataset.image,
        sizes: JSON.parse(option.dataset.sizes || '[]')
    };

    // Update size options
    const sizeGroup = document.getElementById('size-group');
    const sizeSelect = document.getElementById('size-select');
    sizeSelect.innerHTML = '';

    if (currentProduct.sizes.length > 0) {
        currentProduct.sizes.forEach(size => {
            const opt = document.createElement('option');
            opt.value = size;
            opt.textContent = size;
            sizeSelect.appendChild(opt);
        });
        sizeGroup.style.display = 'block';
    } else {
        sizeGroup.style.display = 'none';
    }

    // Load product image onto canvas
    loadProductImage(currentProduct.imageUrl);
    updatePrice();
    checkAddToCart();
}

function loadProductImage(imageUrl) {
    // Clear canvas but keep logo if exists
    const existingLogo = logoImage;

    canvas.clear();
    canvas.backgroundColor = '#f5f5f5';

    fabric.Image.fromURL(imageUrl, function(img) {
        // Scale to fit canvas
        const scale = Math.min(
            (canvas.width - 40) / img.width,
            (canvas.height - 40) / img.height
        );

        img.set({
            left: canvas.width / 2,
            top: canvas.height / 2,
            originX: 'center',
            originY: 'center',
            scaleX: scale,
            scaleY: scale,
            selectable: false,
            evented: false
        });

        productImage = img;
        canvas.add(img);
        canvas.sendToBack(img);

        // Re-add logo if it existed
        if (existingLogo && uploadedLogoUrl) {
            addLogoToCanvas(uploadedLogoUrl);
        }

        canvas.renderAll();
    }, { crossOrigin: 'anonymous' });
}

function getSelectedLogoMode() {
    const selected = document.querySelector('input[name="logo-mode"]:checked');
    return selected ? selected.value : 'bw';
}

function handleFileUpload(file) {
    // Validate file
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml'];
    if (!validTypes.includes(file.type)) {
        alert('Please upload a PNG, JPG, or SVG file.');
        return;
    }

    if (file.size > 5 * 1024 * 1024) {
        alert('File is too large. Maximum size is 5MB.');
        return;
    }

    // Store original file for reprocessing when mode changes
    originalLogoFile = file;

    // Get selected processing mode
    const mode = getSelectedLogoMode();

    // Upload to server with processing mode
    const formData = new FormData();
    formData.append('logo', file);
    formData.append('mode', mode);

    fetch('/api/upload-logo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }

        uploadedLogoUrl = data.processed_url;
        uploadedLogoFilename = data.filename;

        // Show preview
        document.getElementById('logo-preview').style.display = 'block';
        document.getElementById('logo-preview-img').src = data.processed_url;
        document.getElementById('upload-zone').style.display = 'none';

        // Add to canvas
        addLogoToCanvas(data.processed_url);
        checkAddToCart();
    })
    .catch(error => {
        console.error('Upload error:', error);
        alert('Failed to upload logo. Please try again.');
    });
}

function addLogoToCanvas(imageUrl) {
    // Remove existing logo
    if (logoImage) {
        canvas.remove(logoImage);
    }

    fabric.Image.fromURL(imageUrl, function(img) {
        // Scale logo to reasonable size
        const maxSize = 150;
        const scale = Math.min(maxSize / img.width, maxSize / img.height);

        img.set({
            left: canvas.width / 2,
            top: canvas.height / 2,
            originX: 'center',
            originY: 'center',
            scaleX: scale,
            scaleY: scale,
            cornerColor: '#3498db',
            cornerSize: 10,
            transparentCorners: false,
            borderColor: '#3498db',
            borderScaleFactor: 2
        });

        logoImage = img;
        canvas.add(img);
        canvas.setActiveObject(img);
        canvas.renderAll();
    }, { crossOrigin: 'anonymous' });
}

function resetLogoPosition() {
    if (logoImage) {
        logoImage.set({
            left: canvas.width / 2,
            top: canvas.height / 2,
            scaleX: 0.5,
            scaleY: 0.5,
            angle: 0
        });
        canvas.renderAll();
    }
}

function zoomIn() {
    if (logoImage) {
        logoImage.set({
            scaleX: logoImage.scaleX * 1.1,
            scaleY: logoImage.scaleY * 1.1
        });
        canvas.renderAll();
    }
}

function zoomOut() {
    if (logoImage) {
        logoImage.set({
            scaleX: logoImage.scaleX * 0.9,
            scaleY: logoImage.scaleY * 0.9
        });
        canvas.renderAll();
    }
}

function deleteSelected() {
    if (logoImage) {
        canvas.remove(logoImage);
        logoImage = null;
        uploadedLogoUrl = null;
        uploadedLogoFilename = null;
        originalLogoFile = null;

        // Reset upload UI
        document.getElementById('logo-preview').style.display = 'none';
        document.getElementById('upload-zone').style.display = 'block';

        canvas.renderAll();
        checkAddToCart();
    }
}

function updatePrice() {
    const quantity = parseInt(document.getElementById('quantity').value) || 1;
    const unitPrice = currentProduct ? currentProduct.price : 0;
    const total = unitPrice * quantity;

    document.getElementById('unit-price').textContent = '$' + unitPrice.toFixed(2);
    document.getElementById('qty-display').textContent = quantity;
    document.getElementById('total-price').textContent = '$' + total.toFixed(2);
}

function checkAddToCart() {
    const btn = document.getElementById('add-to-cart-btn');
    const canAdd = currentProduct && logoImage && uploadedLogoFilename;
    btn.disabled = !canAdd;
}

function getLogoPosition() {
    if (!logoImage) return null;
    return {
        left: logoImage.left,
        top: logoImage.top,
        scaleX: logoImage.scaleX,
        scaleY: logoImage.scaleY,
        angle: logoImage.angle
    };
}

function getPreviewDataUrl() {
    return canvas.toDataURL({
        format: 'png',
        quality: 0.8
    });
}

function addToCart() {
    if (!currentProduct || !uploadedLogoFilename) {
        alert('Please select a product and upload a logo.');
        return;
    }

    const sizeSelect = document.getElementById('size-select');
    const quantity = parseInt(document.getElementById('quantity').value) || 1;

    const data = {
        product_id: currentProduct.id,
        size: sizeSelect.value || null,
        quantity: quantity,
        logo_filename: uploadedLogoFilename,
        logo_position: getLogoPosition(),
        preview_data_url: getPreviewDataUrl()
    };

    fetch('/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.error) {
            alert(result.error);
            return;
        }

        // Update cart count
        const badge = document.getElementById('cart-count');
        badge.textContent = result.cart_count;
        badge.style.display = 'inline';

        // Show success message
        alert('Added to cart!');

        // Optionally redirect to cart
        // window.location.href = '/cart';
    })
    .catch(error => {
        console.error('Add to cart error:', error);
        alert('Failed to add to cart. Please try again.');
    });
}
