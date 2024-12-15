from flask import Flask, request, jsonify, render_template
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes, OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image
import os
from datetime import datetime
import base64
import io
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import logging
import json
import time  # Add time module for retry logic
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

app = Flask(__name__)

# Azure credentials
ENDPOINT = os.getenv('AZURE_ENDPOINT')
KEY = os.getenv('AZURE_KEY')
INSTRUMENTATION_KEY = os.getenv('AZURE_INSTRUMENTATION_KEY')

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
        image_data = data.get('image_data', '')
        mode = data.get('mode', 'image')
        language = data.get('language', 'en')
        
        logging.info(f"Analyzing image in mode: {mode}")
        
        try:
            # Check if the input is a URL
            if isinstance(image_data, str) and (image_data.startswith('http://') or image_data.startswith('https://')):
                # Use URL directly with Azure
                if mode == 'text':
                    results = detect_text_from_url(image_data, language)
                else:
                    results = analyze_image_from_url(image_data, language)
            else:
                # Handle base64 image data
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                
                # Convert base64 to image stream
                image_bytes = base64.b64decode(image_data)
                image_stream = io.BytesIO(image_bytes)
                
                if mode == 'text':
                    results = detect_text_from_image(image_stream, language)
                else:
                    results = analyze_image_from_stream(image_stream, language)
            
            # Save to history
            save_to_history(image_data, results, mode, language)
            return jsonify(results)
            
        except Exception as e:
            logging.error(f"Error in image analysis: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except Exception as e:
        logging.error(f"Error in analyze route: {str(e)}")
        return jsonify({'error': str(e)}), 500

def analyze_image_from_stream(image_stream, language):
    try:
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

        # Process results
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
        return results
    except Exception as e:
        logging.error(f"Error analyzing image: {str(e)}")
        raise

def detect_text_from_image(image_stream, language):
    try:
        # Add retry logic for OCR
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = computervision_client.read_in_stream(image_stream, raw=True)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Retry {attempt + 1} after error: {str(e)}")
                time.sleep(retry_delay)
                image_stream.seek(0)

        # Get the operation location
        operation_location = response.headers["Operation-Location"]
        operation_id = operation_location.split('/')[-1]

        # Wait for the operation to complete
        timeout = 30  # seconds
        start_time = time.time()
        
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            if time.time() - start_time > timeout:
                raise TimeoutError("OCR operation timed out")
            time.sleep(1)

        # Process results
        text_results = []
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
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

        return {
            'success': True,
            'text_results': text_results
        }
    except Exception as e:
        logging.error(f"Error detecting text: {str(e)}")
        raise

def analyze_image_from_url(image_url, language):
    try:
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
                response = computervision_client.analyze_image(image_url, visual_features=features)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Retry {attempt + 1} after error: {str(e)}")
                time.sleep(retry_delay)
        
        # Process results
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
        return results
    except Exception as e:
        logging.error(f"Error analyzing image from URL: {str(e)}")
        raise

def detect_text_from_url(image_url, language):
    try:
        # Add retry logic for OCR
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                response = computervision_client.read(image_url, raw=True)
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Retry {attempt + 1} after error: {str(e)}")
                time.sleep(retry_delay)
        
        # Get the operation location
        operation_location = response.headers["Operation-Location"]
        operation_id = operation_location.split('/')[-1]
        
        # Wait for the operation to complete
        timeout = 30  # seconds
        start_time = time.time()
        
        while True:
            read_result = computervision_client.get_read_result(operation_id)
            if read_result.status not in ['notStarted', 'running']:
                break
            if time.time() - start_time > timeout:
                raise TimeoutError("OCR operation timed out")
            time.sleep(1)
        
        # Process results
        text_results = []
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
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
        
        return {
            'success': True,
            'text_results': text_results
        }
    except Exception as e:
        logging.error(f"Error detecting text from URL: {str(e)}")
        raise

@app.route('/fetch_image_url', methods=['POST'])
def fetch_image_url():
    try:
        data = request.get_json()
        image_url = data.get('url')
        
        logging.info(f"Attempting to fetch image from URL: {image_url}")
        
        if not image_url:
            logging.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
            
        # Download the image
        try:
            # Add browser-like headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': image_url,
                'DNT': '1',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(
                image_url,
                stream=True,
                verify=False,
                headers=headers,
                timeout=10
            )
            
            logging.info(f"Response status code: {response.status_code}")
            logging.info(f"Response headers: {response.headers}")
            
            if not response.ok:
                error_msg = f"Failed to fetch image. Status code: {response.status_code}"
                if response.status_code == 403:
                    error_msg += ". The image server denied access. Please try a different image URL."
                logging.error(error_msg)
                return jsonify({'error': error_msg}), 400
                
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logging.error(f"Invalid content type: {content_type}")
                return jsonify({'error': 'URL does not point to a valid image'}), 400
                
            # Convert to base64
            try:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                buffered = io.BytesIO()
                
                # Convert RGBA to RGB if necessary
                if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1])
                    image = background
                
                image.save(buffered, format='JPEG', quality=85)
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                logging.info("Successfully processed image")
                return jsonify({
                    'image_data': f'data:image/jpeg;base64,{img_str}'
                })
            except Exception as e:
                logging.error(f"Error processing image: {str(e)}")
                return jsonify({'error': 'Failed to process image format'}), 400
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {str(e)}")
            return jsonify({'error': 'Failed to fetch image from URL'}), 400
            
    except Exception as e:
        logging.error(f"Error fetching image from URL: {str(e)}")
        return jsonify({'error': 'Failed to process request'}), 500

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
    app.run(host='0.0.0.0', port=8101)