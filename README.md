# Azure Vision Web Application

A modern web application that leverages Azure Computer Vision API for advanced image analysis and text detection. This application provides an intuitive interface for analyzing images and extracting text using Azure's powerful AI capabilities, with support for multiple languages and themes.

## Features

### 1. Image Recognition Mode
- Image description generation
- Object detection with confidence scores
- Color analysis (dominant colors, accent color, B&W detection)
- Results visualization with confidence indicators

### 2. Text Detection (OCR) Mode
- Text extraction from images
- Confidence scores for detected text
- Support for multiple languages
- Clear text results display

### 3. Multilingual Support
- Interface available in:
  - English (default)
  - French
  - Arabic
- Full translation of:
  - UI elements
  - Analysis results
  - Color names
- RTL support for Arabic

### 4. Theme Support
- Light and dark mode themes
- Persistent theme selection
- Smooth theme transitions
- Automatic theme preference saving

### 5. History Feature
- Saves all analysis results
- View past analyses with timestamps
- Includes original images and results
- Clear history functionality

## Prerequisites

- Python 3.11 or higher
- Azure Cognitive Services account
- Azure Computer Vision API key and endpoint

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd azure-vision-app
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Azure credentials:
```env
AZURE_ENDPOINT=your_azure_endpoint
AZURE_KEY=your_azure_api_key
```

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:8080
```

## Usage

### Image Analysis
1. Click "Image Recognition" mode
2. Upload an image by dragging and dropping or clicking the upload area
3. Click "Analyze Image"
4. View results including description, objects, and colors

### Text Detection
1. Switch to "Text Detection" mode
2. Upload an image containing text
3. Click "Detect Text"
4. View extracted text with confidence scores

### Language Selection
1. Use the language toggle in the top-left corner
2. Choose between English, French, or Arabic
3. UI and results will update automatically
4. Language preference is saved for future visits

### Theme Selection
1. Click the theme toggle in the top-right corner
2. Switch between light and dark modes
3. Theme preference is saved for future visits

### History
1. Click the "History" tab to view past analyses
2. Each history card shows:
   - Original image
   - Analysis type
   - Timestamp
   - Results summary
3. Use "Clear History" to remove all past analyses

## Project Structure

```
azure-vision-app/
├── app.py              # Main Flask application
├── static/
│   └── style.css      # CSS styles with theme support
├── templates/
│   └── index.html     # Main HTML template
├── history/           # Analysis history storage
└── .env              # Environment variables
```

## Dependencies

- Flask
- azure-cognitiveservices-vision-computervision
- python-dotenv
- Pillow
- deep-translator
- msrest

## Error Handling

The application includes comprehensive error handling for:
- Invalid image uploads
- API failures
- Network issues
- History management errors
- Translation errors

## Security Considerations

- Environment variables for sensitive data
- Input validation
- Secure file handling
- No direct file system access

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Azure Computer Vision API
- Flask Framework
- Font Awesome Icons
- Google Translator API
