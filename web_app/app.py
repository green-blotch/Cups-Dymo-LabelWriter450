#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
from PIL import Image, ImageDraw, ImageFont
import cups
import tempfile
import os

app = Flask(__name__)

# Common Dymo label sizes (in mm and CUPS points)
LABEL_SIZES = {
    '11354': {'name': '2-1/4" x 1-1/4" (57x32mm) Multipurpose', 'width_mm': 57, 'height_mm': 32, 'cups': 'w162h90'},
    '30252': {'name': '1-1/8" x 3-1/2" (28x89mm) Address', 'width_mm': 28, 'height_mm': 89, 'cups': 'w79h252'},
    '30323': {'name': '2-1/8" x 4" (54x101mm) Shipping', 'width_mm': 54, 'height_mm': 101, 'cups': 'w153h286'},
    '30256': {'name': '2-5/16" x 4" (59x101mm) Shipping', 'width_mm': 59, 'height_mm': 101, 'cups': 'w167h286'},
    '99012': {'name': '3-1/2" x 1-1/8" (89x36mm) Large Address', 'width_mm': 89, 'height_mm': 36, 'cups': 'w252h102'},
}

def create_label_image(text, label_size, font_size, align):
    """Create a label image with the specified text and settings"""
    size_info = LABEL_SIZES.get(label_size, LABEL_SIZES['11354'])
    
    # Convert mm to pixels at 300 DPI
    dpi = 300
    width_px = int(size_info['width_mm'] * dpi / 25.4)
    height_px = int(size_info['height_mm'] * dpi / 25.4)
    
    # Create image
    img = Image.new('RGB', (width_px, height_px), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a better font, fall back to default if not available
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position based on alignment
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    if align == 'left':
        x = 20
    elif align == 'center':
        x = (width_px - text_width) // 2
    else:  # right
        x = width_px - text_width - 20
    
    y = (height_px - text_height) // 2
    
    # Draw text
    draw.text((x, y), text, fill='black', font=font)
    
    return img

@app.route('/')
def index():
    return render_template('index.html', label_sizes=LABEL_SIZES)

@app.route('/preview', methods=['POST'])
def preview():
    """Generate a preview of the label"""
    data = request.json
    text = data.get('text', 'Sample Text')
    label_size = data.get('label_size', '11354')
    font_size = int(data.get('font_size', 40))
    align = data.get('align', 'center')
    
    # Create label image
    img = create_label_image(text, label_size, font_size, align)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img.save(tmp.name, 'PNG')
        tmp_path = tmp.name
    
    # Return success (in production, you'd return the image)
    return jsonify({'success': True, 'message': 'Preview generated'})

@app.route('/print', methods=['POST'])
def print_label():
    """Print the label"""
    try:
        data = request.json
        text = data.get('text', '')
        label_size = data.get('label_size', '11354')
        font_size = int(data.get('font_size', 40))
        align = data.get('align', 'center')
        copies = int(data.get('copies', 1))
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        # Create label image
        img = create_label_image(text, label_size, font_size, align)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name, 'PNG')
            tmp_path = tmp.name
        
        # Print using CUPS
        conn = cups.Connection()
        size_info = LABEL_SIZES.get(label_size, LABEL_SIZES['11354'])
        
        job_id = conn.printFile(
            'dymo',
            tmp_path,
            'Label',
            {
                'media': size_info['cups'],
                'fit-to-page': 'True',
                'copies': str(copies)
            }
        )
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return jsonify({
            'success': True,
            'message': f'Print job {job_id} submitted successfully',
            'job_id': job_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
