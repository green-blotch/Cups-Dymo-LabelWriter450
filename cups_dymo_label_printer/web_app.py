"""
Flask web application for Dymo label printing.

Provides a web interface for designing and printing labels.
"""

from io import BytesIO
import base64
from flask import Flask, render_template, request, jsonify

from .config import LABEL_SIZES, DEFAULT_LABEL_SIZE, DEFAULT_FONT_SIZE
from .label_generator import create_label_image
from .printer_service import PrinterService


app = Flask(__name__)
printer_service = PrinterService()


@app.route('/')
def index():
    """Render the main label design page."""
    return render_template('index.html', label_sizes=LABEL_SIZES)


@app.route('/preview', methods=['POST'])
def preview():
    """
    Generate a preview of the label as a base64-encoded PNG image.
    
    Returns the image data URL that can be directly used in an <img> src attribute.
    """
    try:
        data = request.json
        text = data.get('text', 'Sample Text')
        label_size = data.get('label_size', DEFAULT_LABEL_SIZE)
        font_size = int(data.get('font_size', DEFAULT_FONT_SIZE))
        align = data.get('align', 'center')
        
        # Create label image
        image = create_label_image(text, label_size, font_size, align)
        
        # Convert to base64
        buffered = BytesIO()
        image.save(buffered, format='PNG')
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}'
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/print', methods=['POST'])
def print_label():
    """Print a label with the specified parameters."""
    try:
        data = request.json
        text = data.get('text', '')
        label_size = data.get('label_size', DEFAULT_LABEL_SIZE)
        font_size = int(data.get('font_size', DEFAULT_FONT_SIZE))
        align = data.get('align', 'center')
        copies = int(data.get('copies', 1))
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        # Create label image
        image = create_label_image(text, label_size, font_size, align)
        
        # Print the label
        job_id = printer_service.print_image(image, label_size, copies, 'Label')
        
        return jsonify({
            'success': True,
            'message': f'Print job {job_id} submitted successfully',
            'job_id': job_id
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/status', methods=['GET'])
def printer_status():
    """Get the current printer status."""
    status = printer_service.get_printer_status()
    return jsonify(status)


def run_app(host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
    """
    Run the Flask application.
    
    Args:
        host: Host address to bind to
        port: Port number to listen on
        debug: Enable debug mode
    """
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_app()
