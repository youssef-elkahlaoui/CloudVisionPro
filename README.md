# Cloud Vision Application

A Flask-based web application that leverages Azure Computer Vision for image analysis and Azure Monitor for application monitoring.

## Architecture
The application follows a three-tier architecture:
- Client Layer: Web interface for image upload and result display
- Server Layer: Flask application with REST API endpoints
- Cloud Layer: Azure services for image processing and monitoring

For detailed architecture visualization, see `architecture.d2`.

## Features
- 🖼️ Image Analysis
  - Object detection
  - Text extraction
  - Color analysis
- 🌍 Multi-language Support
  - Dynamic translation of results
  - Support for multiple target languages
- 📊 Monitoring & Logging
  - Azure Monitor integration
  - Real-time metrics
  - Custom log analytics
- 📝 History Management
  - Save analysis results
  - View historical analyses
  - Clear history functionality

## Prerequisites
- Python 3.8+
- Azure account with:
  - Computer Vision API subscription
  - Azure Monitor workspace
  - Log Analytics workspace

## Environment Setup
1. Create a `.env` file with:
```env
# Azure Computer Vision
AZURE_KEY=your_vision_api_key
AZURE_ENDPOINT=your_vision_endpoint

# Azure Monitor
AZURE_DATA_COLLECTION_ENDPOINT=your_monitor_endpoint
AZURE_RULE_ID=your_rule_id
AZURE_STREAM_NAME=your_stream_name
AZURE_WORKSPACE_ID=your_workspace_id
```

## Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application
1. Start the Flask server:
```bash
python app.py
```
2. Access the application at `http://localhost:8000`

## API Endpoints
- `GET /`: Main application interface
- `POST /analyze`: Image analysis endpoint
  - Accepts: Base64 encoded image
  - Returns: Analysis results
- `GET /history`: View analysis history
- `POST /clear_history`: Clear analysis history
- `GET /logs`: View application logs

## Monitoring
The application uses Azure Monitor for comprehensive monitoring:
1. Application Logs
   - API endpoint access
   - Analysis operations
   - Error tracking
2. Performance Metrics
   - Response times
   - Request counts
   - Error rates
3. Custom Metrics
   - Image processing times
   - Translation performance
   - API call success rates

## Project Structure
```
Cloud/
├── app.py              # Main Flask application
├── azure_monitor.py    # Azure monitoring configuration
├── requirements.txt    # Python dependencies
├── architecture.d2     # Architecture diagram
├── .env               # Environment variables
└── static/            # Static files
    └── history/       # Analysis history storage
```

## Error Handling
- Comprehensive error handling for:
  - Invalid image formats
  - API failures
  - Network issues
  - Invalid requests

## Security
- Environment variable based configuration
- Azure authentication handling
- Input validation
- Error message sanitization

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
- Azure Monitor Services
