from flask import Flask, request, jsonify, render_template
import os
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
import io
import base64
from dotenv import load_dotenv
import time
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# Azure Configuration
endpoint = os.getenv('AZURE_ENDPOINT')
subscription_key = os.getenv('AZURE_KEY')

# Initialize the Computer Vision client
computervision_client = ComputerVisionClient(
    endpoint,
    CognitiveServicesCredentials(subscription_key)
)

# Create history directory if it doesn't exist
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history')
if not os.path.exists(HISTORY_DIR):
    os.makedirs(HISTORY_DIR)
    logger.info(f"Created history directory at {HISTORY_DIR}")

def save_to_history(image_data, results, mode):
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_file = os.path.join(HISTORY_DIR, f'analysis_{timestamp}.json')
        
        # Clean up base64 image data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        history_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': mode,
            'image': image_data,
            'results': results
        }
        
        with open(history_file, 'w') as f:
            json.dump(history_data, f)
        logger.info(f"Successfully saved history to {history_file}")
        return True
    except Exception as e:
        logger.error(f"Error saving history: {str(e)}")
        return False

def get_history(limit=10):
    try:
        if not os.path.exists(HISTORY_DIR):
            logger.warning("History directory does not exist")
            return []
            
        history_files = sorted(
            [f for f in os.listdir(HISTORY_DIR) if f.startswith('analysis_')],
            reverse=True
        )[:limit]
        
        history = []
        for file in history_files:
            try:
                with open(os.path.join(HISTORY_DIR, file), 'r') as f:
                    history.append(json.load(f))
                logger.debug(f"Loaded history file: {file}")
            except Exception as e:
                logger.error(f"Error loading history file {file}: {str(e)}")
                continue
        
        return history
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return []

def process_image_data(image_data):
    try:
        # Remove the data URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 string to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Create a BytesIO object
        image_stream = io.BytesIO(image_bytes)
        logger.debug("Successfully processed image data")
        return image_stream
    except Exception as e:
        logger.error(f"Error processing image data: {str(e)}")
        raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get image data and mode from request
        image_data = request.form.get('image')
        mode = request.form.get('mode', 'image')  # Default to image mode
        
        if not image_data:
            logger.warning("No image data provided")
            return jsonify({'success': False, 'error': 'No image provided'})

        # Process image data
        image_stream = process_image_data(image_data)
        
        if mode == 'image':
            # Analyze image for objects and description
            features = [
                VisualFeatureTypes.description,
                VisualFeatureTypes.objects,
                VisualFeatureTypes.color
            ]
            
            response = computervision_client.analyze_image_in_stream(
                image_stream,
                visual_features=features
            )

            # Extract results
            results = {
                'success': True,
                'description': response.description.captions[0].text if response.description.captions else 'No description available',
                'objects': [
                    {
                        'name': obj.object_property,
                        'confidence': obj.confidence
                    } for obj in response.objects
                ],
                'colors': {
                    'dominant_colors': response.color.dominant_colors,
                    'accent_color': response.color.accent_color,
                    'is_bw': response.color.is_bw_img
                }
            }

        else:  # Text detection mode
            # First start the OCR operation
            response = computervision_client.read_in_stream(
                image_stream,
                raw=True
            )

            # Get the operation location from the response headers
            operation_location = response.headers["Operation-Location"]
            operation_id = operation_location.split('/')[-1]

            # Wait for the operation to complete
            while True:
                read_result = computervision_client.get_read_result(operation_id)
                if read_result.status not in ['notStarted', 'running']:
                    break
                time.sleep(1)

            # Extract text results
            text_results = []
            if read_result.status == OperationStatusCodes.succeeded:
                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        text_results.append({
                            'text': line.text,
                            'confidence': line.confidence if hasattr(line, 'confidence') else 1.0
                        })

            results = {
                'success': True,
                'text_results': text_results
            }

        # Save to history
        if not save_to_history(image_data, results, mode):
            logger.warning("Failed to save to history")
        
        return jsonify(results)

    except Exception as e:
        logger.error(f"Error in analyze route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/history', methods=['GET'])
def history():
    try:
        history_data = get_history()
        logger.info(f"Retrieved {len(history_data)} history items")
        return jsonify({'success': True, 'history': history_data})
    except Exception as e:
        logger.error(f"Error in history route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        if os.path.exists(HISTORY_DIR):
            for file in os.listdir(HISTORY_DIR):
                if file.startswith('analysis_'):
                    os.remove(os.path.join(HISTORY_DIR, file))
            logger.info("Successfully cleared history")
        return jsonify({'success': True, 'message': 'History cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=8080)