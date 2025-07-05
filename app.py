from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# Using environment variable for API key (more secure)
OCR_API_KEY = os.environ.get('OCR_API_KEY', 'K89559624088957')



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Get language from form data
    language = request.form.get('language', 'eng')
    
    try:
        # Send directly to OCR.space API without saving to disk
        response = requests.post(
            'https://api.ocr.space/parse/image',
            files={'file': file},
            data={
                'apikey': OCR_API_KEY,
                'language': language,
                'isOverlayRequired': False
            }
        )
        
        # Process response
        result = response.json()
        
        # Check for errors
        if result.get('IsErroredOnProcessing', False):
            error_message = result.get('ErrorMessage', 'OCR processing failed')
            return jsonify({'error': error_message}), 500
            
        # Success - extract text
        if 'ParsedResults' in result and len(result['ParsedResults']) > 0:
            extracted_text = result['ParsedResults'][0]['ParsedText']
            return jsonify({'text': extracted_text})
        else:
            return jsonify({'error': 'No text found in the image'}), 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For Vercel deployment
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)