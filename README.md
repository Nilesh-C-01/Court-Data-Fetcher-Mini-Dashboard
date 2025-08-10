Court Data Fetcher & Mini-Dashboard
A web application that fetches and displays case information from Indian courts with a simple and intuitive interface.

🏛️ Court Chosen
Delhi High Court (https://delhihighcourt.nic.in/)

✨ Features
Simple web interface for case lookup

Support for multiple case types and filing years

Automated data extraction from court website

PDF download functionality for orders/judgments

SQLite database logging of all queries

Error handling for invalid cases and site issues

💻 Tech Stack
Backend: Python Flask

Frontend: HTML, CSS, JavaScript, Bootstrap

Database: SQLite

Web Scraping: Requests, BeautifulSoup4, Selenium WebDriver

PDF Handling: PyPDF2

🚀 Setup Instructions
Prerequisites
Python 3.8+

Chrome/Chromium browser

ChromeDriver (automatically managed by webdriver-manager)

Installation
Clone the repository:

git clone https://github.com/Nilesh-C-01/court-data-fetcher.git
cd court-data-fetcher

Create a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Set up environment variables:

cp .env.example .env
# Edit .env file with your configurations

Initialize the database:

python init_db.py

Run the application:

python app.py

Visit http://localhost:5000 to access the application.

⚙️ Environment Variables
# Database Configuration
DATABASE_PATH=court_data.db
DEBUG=True

# Scraping Configuration
SELENIUM_TIMEOUT=30
MAX_RETRIES=3
REQUEST_DELAY=2

# Security
SECRET_KEY=your-secret-key-here

🔒 CAPTCHA Strategy
The Delhi High Court case status page uses a numeric text CAPTCHA. Our script automatically handles this by:

Locating the <span> element with the numeric CAPTCHA.

Extracting the numeric CAPTCHA text directly from the DOM.

Filling it programmatically into the form.

No manual input or external OCR service is needed, since the CAPTCHA is already plain text.

Note: If the Delhi High Court changes the CAPTCHA to image-based, the script would need to be updated to use a different strategy, such as OCR with Tesseract or a manual token input field.

🔌 API Endpoints
GET / - Main dashboard

POST /search - Search for case information

GET /download/<file_id> - Download PDF files

GET /history - View search history

GET /api/case/<case_number> - REST API for case data

🗃️ Database Schema
-- Cases table
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_type VARCHAR(100),
    case_number VARCHAR(100),
    filing_year INTEGER,
    search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    response_data TEXT,
    status VARCHAR(50)
);

-- Case details table
CREATE TABLE case_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    parties_plaintiff TEXT,
    parties_defendant TEXT,
    filing_date DATE,
    next_hearing_date DATE,
    case_status VARCHAR(100),
    FOREIGN KEY (case_id) REFERENCES cases (id)
);

-- Orders table
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    order_date DATE,
    order_type VARCHAR(100),
    pdf_url TEXT,
    local_pdf_path TEXT,
    FOREIGN KEY (case_id) REFERENCES cases (id)
);

📝 Usage Examples
Basic Search:

Select case type (e.g., "Civil Appeal")

Enter case number (e.g., "123/2023")

Select filing year

Click "Search Case"

Download PDFs:

Click on any order/judgment link

PDF will be downloaded automatically

View History:

Navigate to /history to see all previous searches

⚠️ Error Handling
Invalid case numbers show user-friendly error messages

Network timeouts are handled gracefully

Database errors are logged and don't crash the application

CAPTCHA detection triggers the automated solving workflow

✅ Testing
Run unit tests:

python -m pytest tests/ -v

Run integration tests:

python -m pytest tests/integration/ -v

🐳 Docker Support
Build and run with Docker:

docker build -t court-data-fetcher .
docker run -p 5000:5000 court-data-fetcher

🤝 Contributing
Fork the repository

Create a feature branch

Commit your changes

Push to the branch

Create a Pull Request

📜 Legal Compliance
This tool only accesses publicly available information from court websites. It respects robots.txt and implements reasonable request throttling. Users are responsible for complying with the court website's terms of service.

📄 License
MIT License - see the LICENSE file for details.

🆘 Support
If you encounter issues:

Check the logs in logs/app.log

Ensure all dependencies are installed

Verify the court website is accessible

Check your internet connection

🗺️ Roadmap
[ ] Support for multiple courts

[ ] Advanced search filters

[ ] Email notifications for case updates

[ ] Mobile-responsive design improvements

[ ] API authentication and rate limiting
