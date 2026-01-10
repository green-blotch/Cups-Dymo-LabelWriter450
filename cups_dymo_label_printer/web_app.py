"""
Flask web application for Dymo label printing.

Provides a web interface for designing and printing labels.
"""

from io import BytesIO
import base64
import json
import os
import uuid
from flask import Flask, render_template, request, jsonify

from .config import LABEL_SIZES, DEFAULT_LABEL_SIZE, DEFAULT_FONT_SIZE
from .label_generator import create_label_image
from .printer_service import PrinterService


app = Flask(__name__)
printer_service = PrinterService()
_MEMORY_FILE = os.getenv('LABEL_MEMORY_FILE', 'saved_labels.json')
_saved_labels: list[dict] = []  # in-memory stack of saved labels


def _label_key(payload: dict) -> tuple:
    """Generate a hashable key for deduplication of saved labels."""
    return (
        payload.get('text', ''),
        payload.get('label_size', DEFAULT_LABEL_SIZE),
        int(payload.get('font_size', DEFAULT_FONT_SIZE)),
        payload.get('align', 'center'),
        int(payload.get('copies', 1)),
    )


def _save_label(payload: dict) -> dict:
    """Save label payload to stack, deduplicating and moving to top."""
    global _saved_labels
    key = _label_key(payload)
    # Remove any existing matching entry
    _saved_labels = [entry for entry in _saved_labels if _label_key(entry) != key]
    new_entry = {
        'id': str(uuid.uuid4()),
        'text': payload.get('text', ''),
        'label_size': payload.get('label_size', DEFAULT_LABEL_SIZE),
        'font_size': int(payload.get('font_size', DEFAULT_FONT_SIZE)),
        'align': payload.get('align', 'center'),
        'copies': int(payload.get('copies', 1)),
    }
    _saved_labels.insert(0, new_entry)
    _persist_memory()
    return new_entry


def _delete_labels(ids: list[str]) -> None:
    """Delete labels by id from the saved stack."""
    global _saved_labels
    id_set = set(ids)
    _saved_labels = [entry for entry in _saved_labels if entry['id'] not in id_set]
    _persist_memory()


def _persist_memory() -> None:
    try:
        with open(_MEMORY_FILE, 'w', encoding='utf-8') as fh:
            json.dump(_saved_labels, fh)
    except Exception:
        # Fail-soft on persistence errors
        pass


def _load_memory() -> None:
    global _saved_labels
    if not _MEMORY_FILE or not os.path.exists(_MEMORY_FILE):
        _saved_labels = []
        return
    try:
        with open(_MEMORY_FILE, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
            if isinstance(data, list):
                _saved_labels = data
    except Exception:
        _saved_labels = []


_load_memory()


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

        # Save to memory stack (dedup + move to top)
        _save_label(data)
        
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


@app.route('/memory', methods=['GET', 'DELETE'])
def memory():
    """Manage in-memory saved labels stack."""
    if request.method == 'GET':
        return jsonify(_saved_labels)

    # DELETE selected ids
    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list):
        return jsonify({'success': False, 'error': 'ids must be a list'}), 400
    _delete_labels([str(i) for i in ids])
    return jsonify({'success': True, 'remaining': _saved_labels})


def run_app(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
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
