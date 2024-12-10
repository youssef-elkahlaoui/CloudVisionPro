from flask import Flask, request, jsonify, render_template, url_for
from PIL import Image
import os
from datetime import datetime
import base64
import io
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import logging
import json
import time

# Azure computer vision
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes, OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials

# Azure Monitor imports
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.trace.samplers import ProbabilitySampler

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add Azure Monitor logging
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING'))
)

load_dotenv()

app = Flask(__name__)

# Initialize Azure Monitor
middleware = FlaskMiddleware(
    app,
    exporter=AzureExporter(connection_string=os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')),
    sampler=ProbabilitySampler(rate=1.0)
)

# Azure credentials
ENDPOINT = os.getenv('AZURE_ENDPOINT')
KEY = os.getenv('AZURE_KEY')

# Initialize Azure client
computervision_client = ComputerVisionClient(
    ENDPOINT, CognitiveServicesCredentials(KEY))

# Color translations
color_translations = {
    'fr': {
        'black': 'noir',
        'white': 'blanc',
        'red': 'rouge',
        'blue': 'bleu',
        'green': 'vert',
        'yellow': 'jaune',
        'purple': 'violet',
        'orange': 'orange',
        'gray': 'gris',
        'brown': 'marron',
        'pink': 'rose',
        'gold': 'or',
        'silver': 'argent',
        'beige': 'beige',
        'navy': 'bleu marine',
        'teal': 'bleu sarcelle'
    },
    'ar': {
        'black': 'أسود',
        'white': 'أبيض',
        'red': 'أحمر',
        'blue': 'أزرق',
        'green': 'أخضر',
        'yellow': 'أصفر',
        'purple': 'بنفسجي',
        'orange': 'برتقالي',
        'gray': 'رمادي',
        'brown': 'بني',
        'pink': 'وردي',
        'gold': 'ذهبي',
        'silver': 'فضي',
        'beige': 'بيج',
        'navy': 'كحلي',
        'teal': 'أزرق مخضر'
    }
}

# Constants for history management
HISTORY_DIR = 'history'
HISTORY_FILE = os.path.join(HISTORY_DIR, 'history.json')

def translate_text(text, target_lang):
    if target_lang == 'en':
        return text
    try:
        translator = GoogleTranslator(source='en', target=target_lang)
        return translator.translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text
        
def translate_color(color, target_lang):
    if target_lang == 'en':
        return color
    try:
        return color_translations[target_lang].get(color.lower(), color)
    except:
        return color

def save_to_history(image_data, results, mode, language):
    try:
        # Ensure history directory exists
        os.makedirs(HISTORY_DIR, exist_ok=True)
        
        # Load existing history
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except json.JSONDecodeError:
                logging.error("Error reading history file. Starting with empty history.")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Clean up base64 image data
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        history_data = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'mode': mode,
            'language': language,
            'image': image_data,
            'results': results
        }
        
        history.append(history_data)
        
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=4)
        logging.info(f"Successfully saved history to {HISTORY_FILE}")
        return True
    except Exception as e:
        logging.error(f"Error saving history: {str(e)}")
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        image_data = data.get('image').split(',')[1]
        mode = data.get('mode', 'image')
        language = data.get('language', 'en')

        # Process image data
        image_bytes = base64.b64decode(image_data)
        image_stream = io.BytesIO(image_bytes)

        if mode == 'image':
            # Analyze image for objects and description
            features = [
                VisualFeatureTypes.description,
                VisualFeatureTypes.objects,
                VisualFeatureTypes.color
            ]
            
            # Add retry logic for better reliability
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = computervision_client.analyze_image_in_stream(
                        image_stream,
                        visual_features=features
                    )
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Retry {attempt + 1} after error: {str(e)}")
                    time.sleep(retry_delay)
                    image_stream.seek(0)  # Reset stream position

            # Extract results
            results = {
                'success': True,
                'description': translate_text(response.description.captions[0].text if response.description.captions else 'No description available', language),
                'objects': [
                    {
                        'name': translate_text(obj.object_property, language),
                        'confidence': obj.confidence
                    } for obj in response.objects
                ],
                'colors': {
                    'dominant_colors': [translate_color(color, language) for color in response.color.dominant_colors],
                    'accent_color': translate_color(response.color.accent_color, language),
                    'is_bw': response.color.is_bw_img
                }
            }

        else:  # Text detection mode
            logging.info("Starting text detection mode")
            # Add retry logic for OCR
            max_retries = 3
            retry_delay = 1  # seconds
            
            for attempt in range(max_retries):
                try:
                    response = computervision_client.read_in_stream(
                        image_stream,
                        raw=True
                    )
                    logging.info("Successfully initiated text detection")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"Failed to initiate text detection after {max_retries} attempts: {str(e)}")
                        raise
                    logging.warning(f"Retry {attempt + 1} after error: {str(e)}")
                    time.sleep(retry_delay)
                    image_stream.seek(0)  # Reset stream position

            # Get the operation location from the response headers
            operation_location = response.headers["Operation-Location"]
            operation_id = operation_location.split('/')[-1]
            logging.info(f"Got operation ID: {operation_id}")

            # Wait for the operation to complete with timeout
            timeout = 30  # seconds
            start_time = time.time()
            
            while True:
                read_result = computervision_client.get_read_result(operation_id)
                logging.info(f"Operation status: {read_result.status}")
                
                if read_result.status not in ['notStarted', 'running']:
                    break
                if time.time() - start_time > timeout:
                    logging.error("OCR operation timed out")
                    raise TimeoutError("OCR operation timed out")
                time.sleep(1)

            # Extract text results
            text_results = []
            if read_result.status == OperationStatusCodes.succeeded:
                logging.info("Text detection succeeded")
                for text_result in read_result.analyze_result.read_results:
                    for line in text_result.lines:
                        # Translate the detected text if language is not English
                        detected_text = line.text
                        if language != 'en':
                            try:
                                detected_text = translate_text(line.text, language)
                            except Exception as e:
                                logging.error(f"Translation error: {str(e)}")
                                # Continue with original text if translation fails
                                pass
                        
                        text_results.append({
                            'text': detected_text,
                            'confidence': line.confidence if hasattr(line, 'confidence') else 1.0
                        })
                        logging.info(f"Detected text: {detected_text} (confidence: {line.confidence if hasattr(line, 'confidence') else 1.0})")
            else:
                logging.warning(f"Text detection failed with status: {read_result.status}")

            results = {
                'success': True,
                'text_results': text_results if text_results else []
            }

        # Save to history
        if not save_to_history(image_data, results, mode, language):
            logging.warning("Failed to save to history")
        
        return jsonify(results)

    except Exception as e:
        logging.error(f"Error in analyze route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/history', methods=['GET'])
def history():
    try:
        history_file = HISTORY_FILE
        if not os.path.exists(history_file):
            return jsonify([])
            
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        return jsonify(history)

    except Exception as e:
        logging.error(f"Error in history route: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/clear-history', methods=['POST'])
def clear_history():
    try:
        history_file = HISTORY_FILE
        if os.path.exists(history_file):
            os.remove(history_file)
        return jsonify({'success': True, 'message': 'History cleared successfully'})

    except Exception as e:
        logging.error(f"Error clearing history: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Use 0.0.0.0 to allow external connections
    app.run(host='0.0.0.0', port=8000)