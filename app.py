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

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    return render_template('disclaimer.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
            
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        language = request.form.get('language', 'eng')
        
        # Validate file
        allowed_ext = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in allowed_ext:
            return jsonify({'error': 'Invalid file format'}), 400
        
        # Read file data
        file.seek(0)
        file_data = file.read()
        if len(file_data) == 0:
            return jsonify({'error': 'Empty file'}), 400
            
        # Try multiple OCR engines
        engines = [2, 1]  # Engine 2 first, then 1 as fallback
        
        for engine in engines:
            try:
                file.seek(0)
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files={'file': (file.filename, file_data, 'image/jpeg')},
                    data={
                        'apikey': OCR_API_KEY,
                        'language': language,
                        'isOverlayRequired': False,
                        'detectOrientation': True,
                        'scale': True,
                        'OCREngine': engine
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if not result.get('IsErroredOnProcessing', False):
                        if 'ParsedResults' in result and result['ParsedResults']:
                            text = result['ParsedResults'][0].get('ParsedText', '').strip()
                            if text:
                                return jsonify({'text': text})
                
            except Exception as e:
                logger.error(f'Engine {engine} failed: {str(e)}')
                continue
        
        return jsonify({'error': 'Could not extract text from image'}), 400
        
    except Exception as e:
        logger.error(f'Upload error: {str(e)}')
        return jsonify({'error': 'Processing failed'}), 500

# For Vercel deployment
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)