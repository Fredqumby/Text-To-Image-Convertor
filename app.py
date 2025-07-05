from flask import Flask, request, jsonify, render_template
import requests
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Using environment variable for API key (more secure)
OCR_API_KEY = os.environ.get('OCR_API_KEY', 'K89559624088957')



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        logger.info('Upload request received')
        
        if 'file' not in request.files:
            logger.error('No file in request')
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if file.filename == '':
            logger.error('Empty filename')
            return jsonify({'error': 'No selected file'}), 400
        
        # Get language from form data
        language = request.form.get('language', 'eng')
        logger.info(f'Processing file: {file.filename}, language: {language}')
        
        # Validate file type
        if not file.filename.lower().endswith('.png'):
            return jsonify({'error': 'Only PNG files are supported'}), 400
        
        # Reset file pointer
        file.seek(0)
        
        # Send directly to OCR.space API without saving to disk
        logger.info('Sending request to OCR.space API')
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': (file.filename, file.read(), 'image/png')},
            data={
                'apikey': OCR_API_KEY,
                'language': language,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2
            },
            timeout=30
        )
        
        logger.info(f'OCR API response status: {response.status_code}')
        
        if response.status_code != 200:
            logger.error(f'OCR API error: {response.status_code} - {response.text}')
            return jsonify({'error': f'OCR service error: {response.status_code}'}), 500
        
        # Process response
        result = response.json()
        logger.info(f'OCR API result: {result}')
        
        # Check for errors
        if result.get('IsErroredOnProcessing', False):
            error_message = result.get('ErrorMessage', 'OCR processing failed')
            logger.error(f'OCR processing error: {error_message}')
            return jsonify({'error': error_message}), 500
            
        # Success - extract text
        if 'ParsedResults' in result and len(result['ParsedResults']) > 0:
            extracted_text = result['ParsedResults'][0]['ParsedText']
            if extracted_text.strip():
                logger.info('Text extraction successful')
                return jsonify({'text': extracted_text})
            else:
                logger.warning('No text found in image')
                return jsonify({'error': 'No text found in the image'}), 400
        else:
            logger.error('No ParsedResults in response')
            return jsonify({'error': 'No text found in the image'}), 400
        
    except requests.exceptions.Timeout:
        logger.error('OCR API timeout')
        return jsonify({'error': 'Request timeout - please try again'}), 500
    except requests.exceptions.RequestException as e:
        logger.error(f'Request error: {str(e)}')
        return jsonify({'error': 'Network error - please check your connection'}), 500
    except Exception as e:
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

# For Vercel deployment
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)