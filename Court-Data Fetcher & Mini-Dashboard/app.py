"""
Court Data Fetcher & Mini-Dashboard
Main Flask application file with enhanced scraper integration
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import traceback

from models import db, Case, CaseDetail, Order
from court_scraper import CourtScraper
from utils import setup_logging, validate_case_number, sanitize_filename

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.getenv('DATABASE_PATH', 'court_data.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create upload folder
UPLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        recent_cases = Case.query.order_by(Case.search_timestamp.desc()).limit(10).all()
        stats = {
            'total_searches': Case.query.count(),
            'successful_searches': Case.query.filter(Case.status == 'success').count(),
            'failed_searches': Case.query.filter(Case.status == 'failed').count()
        }
        return render_template('index.html', recent_cases=recent_cases, stats=stats)
    except Exception as e:
        logger.error(f"Error loading dashboard: {str(e)}")
        flash('Error loading dashboard. Please try again.', 'error')
        return render_template('index.html', recent_cases=[], stats={})

@app.route('/search', methods=['POST'])
def search_case():
    """Handle case search requests with enhanced scraper integration"""
    scraper_instance = None
    try:
        # Get form data
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        filing_year = request.form.get('filing_year', '').strip()
        
        # Validate input
        if not all([case_type, case_number, filing_year]):
            flash('All fields are required', 'error')
            return redirect(url_for('index'))
        
        if not validate_case_number(case_number):
            flash('Invalid case number format', 'error')
            return redirect(url_for('index'))
        
        # Validate year range
        try:
            year_int = int(filing_year)
            current_year = datetime.now().year
            if year_int < 1950 or year_int > current_year:
                flash(f'Filing year must be between 1950 and {current_year}', 'error')
                return redirect(url_for('index'))
        except ValueError:
            flash('Invalid filing year format', 'error')
            return redirect(url_for('index'))
        
        # Check if case already exists in database
        existing_case = Case.query.filter_by(
            case_number=case_number,
            filing_year=year_int,
            case_type=case_type
        ).first()
        
        if existing_case and existing_case.status == 'success':
            flash('Case data already exists in database. Showing cached results.', 'info')
            return redirect(url_for('case_detail', case_id=existing_case.id))
        
        # Create new case record
        case = Case(
            case_type=case_type,
            case_number=case_number,
            filing_year=year_int,
            status='pending'
        )
        db.session.add(case)
        db.session.commit()
        
        logger.info(f"Starting scrape for case: {case_number}/{filing_year} (ID: {case.id})")
        
        # Initialize scraper instance
        scraper_instance = CourtScraper()
        
        # Scrape court data with enhanced error handling
        try:
            scrape_result = scraper_instance.scrape_case_data(case_type, case_number, filing_year)
        except Exception as scrape_error:
            logger.error(f"Scraper execution error: {str(scrape_error)}")
            logger.error(f"Scraper traceback: {traceback.format_exc()}")
            scrape_result = {
                'success': False, 
                'error': f'Scraper execution failed: {str(scrape_error)}'
            }
        
        # Validate scrape result structure
        if not isinstance(scrape_result, dict):
            logger.error(f"Invalid scrape result type: {type(scrape_result)}")
            scrape_result = {'success': False, 'error': 'Invalid response format from scraper'}
        
        # Update case with results
        case.response_data = json.dumps(scrape_result, default=str)  # Handle datetime serialization
        case.status = 'success' if scrape_result.get('success') else 'failed'
        
        if scrape_result.get('success'):
            try:
                # Save case details with enhanced error handling
                parties = scrape_result.get('parties', {})
                case_detail = CaseDetail(
                    case_id=case.id,
                    parties_plaintiff=parties.get('plaintiff', '')[:500],  # Limit length
                    parties_defendant=parties.get('defendant', '')[:500],
                    filing_date=_parse_date(scrape_result.get('filing_date')),
                    next_hearing_date=_parse_date(scrape_result.get('next_hearing')),
                    case_status=scrape_result.get('status', '')[:100]  # Limit length
                )
                db.session.add(case_detail)
                
                # Save orders with enhanced validation
                orders_saved = 0
                for order_data in scrape_result.get('orders', []):
                    try:
                        order = Order(
                            case_id=case.id,
                            order_date=_parse_date(order_data.get('date')),
                            order_type=order_data.get('type', '')[:100],
                            pdf_url=order_data.get('pdf_url', '')[:500]
                        )
                        db.session.add(order)
                        orders_saved += 1
                    except Exception as order_error:
                        logger.warning(f"Failed to save order: {order_error}")
                        continue
                
                logger.info(f"Saved case details and {orders_saved} orders")
                flash('Case data retrieved successfully!', 'success')
                
            except Exception as db_error:
                logger.error(f"Database save error: {str(db_error)}")
                flash('Case found but error saving details. Basic case info saved.', 'warning')
        else:
            error_msg = scrape_result.get('error', 'Unknown error')
            logger.warning(f"Scraping failed for case {case_number}: {error_msg}")
            flash(f"Error retrieving case data: {error_msg}", 'error')
        
        db.session.commit()
        return redirect(url_for('case_detail', case_id=case.id))
        
    except Exception as e:
        logger.error(f"Critical error in search_case: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        flash('A critical error occurred while searching. Please try again.', 'error')
        return redirect(url_for('index'))
    finally:
        # Ensure scraper is properly closed
        if scraper_instance:
            try:
                scraper_instance._close_driver()
            except:
                pass

def _parse_date(date_string):
    """Helper function to parse date strings safely"""
    if not date_string:
        return None
    
    try:
        # Handle different date formats
        if isinstance(date_string, str):
            # Try YYYY-MM-DD format first
            if '-' in date_string and len(date_string) == 10:
                return datetime.strptime(date_string, '%Y-%m-%d').date()
            # Try DD/MM/YYYY format
            elif '/' in date_string and len(date_string) == 10:
                return datetime.strptime(date_string, '%d/%m/%Y').date()
        
        return None
    except ValueError as e:
        logger.warning(f"Date parsing error for '{date_string}': {e}")
        return None

@app.route('/case/<int:case_id>')
def case_detail(case_id):
    """Display detailed case information"""
    try:
        case = Case.query.get_or_404(case_id)
        case_detail = CaseDetail.query.filter_by(case_id=case_id).first()
        orders = Order.query.filter_by(case_id=case_id).all()
        
        # Parse response data for additional debugging info
        response_data = {}
        if case.response_data:
            try:
                response_data = json.loads(case.response_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in response_data for case {case_id}")
        
        return render_template('case_detail.html', 
                             case=case, 
                             case_detail=case_detail, 
                             orders=orders,
                             response_data=response_data)
    except Exception as e:
        logger.error(f"Error loading case detail: {str(e)}")
        flash('Error loading case details', 'error')
        return redirect(url_for('index'))

@app.route('/download/<int:order_id>')
def download_order(order_id):
    """Download PDF order/judgment with enhanced error handling"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Check if file exists locally first
        if order.local_pdf_path and os.path.exists(order.local_pdf_path):
            logger.info(f"Serving local PDF: {order.local_pdf_path}")
            return send_file(order.local_pdf_path, as_attachment=True)
        
        # Download from URL if available
        elif order.pdf_url:
            logger.info(f"Downloading PDF from URL: {order.pdf_url}")
            
            # Initialize scraper for PDF download
            pdf_scraper = CourtScraper()
            try:
                pdf_content = pdf_scraper.download_pdf(order.pdf_url)
                
                if pdf_content:
                    # Generate safe filename
                    case = Case.query.get(order.case_id)
                    date_str = order.order_date.strftime('%Y-%m-%d') if order.order_date else 'unknown'
                    filename = f"{sanitize_filename(case.case_number)}_{sanitize_filename(order.order_type)}_{date_str}.pdf"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    
                    # Save PDF locally
                    with open(filepath, 'wb') as f:
                        f.write(pdf_content)
                    
                    # Update order with local path
                    order.local_pdf_path = filepath
                    db.session.commit()
                    
                    logger.info(f"PDF saved locally: {filepath}")
                    return send_file(filepath, as_attachment=True, download_name=filename)
                else:
                    flash('Failed to download PDF from court website', 'error')
            finally:
                # Ensure scraper cleanup
                try:
                    pdf_scraper._close_driver()
                except:
                    pass
        else:
            flash('No PDF URL available for this order', 'error')
        
        return redirect(url_for('case_detail', case_id=order.case_id))
        
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        logger.error(f"Download traceback: {traceback.format_exc()}")
        flash('Error downloading PDF. Please try again.', 'error')
        return redirect(url_for('case_detail', case_id=order.case_id) if 'order' in locals() else url_for('index'))

@app.route('/history')
def history():
    """Display search history with enhanced pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Limit max per page
        
        cases = Case.query.order_by(Case.search_timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        return render_template('history.html', cases=cases)
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        flash('Error loading search history', 'error')
        return render_template('history.html', cases=None)

@app.route('/api/case/<case_number>')
def api_case_data(case_number):
    """REST API endpoint for case data with enhanced response"""
    try:
        case = Case.query.filter_by(case_number=case_number).order_by(Case.search_timestamp.desc()).first()
        
        if not case:
            return jsonify({'error': 'Case not found'}), 404
        
        case_detail = CaseDetail.query.filter_by(case_id=case.id).first()
        orders = Order.query.filter_by(case_id=case.id).all()
        
        response_data = {
            'case_id': case.id,
            'case_number': case.case_number,
            'case_type': case.case_type,
            'filing_year': case.filing_year,
            'status': case.status,
            'search_timestamp': case.search_timestamp.isoformat(),
            'details': {
                'parties_plaintiff': case_detail.parties_plaintiff if case_detail else None,
                'parties_defendant': case_detail.parties_defendant if case_detail else None,
                'filing_date': case_detail.filing_date.isoformat() if case_detail and case_detail.filing_date else None,
                'next_hearing_date': case_detail.next_hearing_date.isoformat() if case_detail and case_detail.next_hearing_date else None,
                'case_status': case_detail.case_status if case_detail else None
            },
            'orders': [{
                'id': order.id,
                'order_date': order.order_date.isoformat() if order.order_date else None,
                'order_type': order.order_type,
                'pdf_url': order.pdf_url,
                'has_local_file': bool(order.local_pdf_path and os.path.exists(order.local_pdf_path)),
                'download_url': url_for('download_order', order_id=order.id)
            } for order in orders]
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in API endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/search', methods=['POST'])
def api_search_case():
    """API endpoint for case search"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        case_type = data.get('case_type', '').strip()
        case_number = data.get('case_number', '').strip()
        filing_year = data.get('filing_year', '').strip()
        
        if not all([case_type, case_number, filing_year]):
            return jsonify({'error': 'All fields are required'}), 400
        
        # Validate and convert year
        try:
            year_int = int(filing_year)
        except ValueError:
            return jsonify({'error': 'Invalid filing year'}), 400
        
        # Check for existing case
        existing_case = Case.query.filter_by(
            case_number=case_number,
            filing_year=year_int,
            case_type=case_type
        ).first()
        
        if existing_case and existing_case.status == 'success':
            return jsonify({
                'success': True,
                'message': 'Case found in database',
                'case_id': existing_case.id,
                'cached': True
            })
        
        # Create new case and scrape
        case = Case(
            case_type=case_type,
            case_number=case_number,
            filing_year=year_int,
            status='pending'
        )
        db.session.add(case)
        db.session.commit()
        
        # Perform scraping
        scraper_instance = CourtScraper()
        try:
            scrape_result = scraper_instance.scrape_case_data(case_type, case_number, filing_year)
            
            # Process and save results
            success = _process_scrape_result(case, scrape_result)
            
            return jsonify({
                'success': success,
                'case_id': case.id,
                'message': 'Case data retrieved successfully' if success else scrape_result.get('error', 'Unknown error'),
                'cached': False
            })
            
        finally:
            try:
                scraper_instance._close_driver()
            except:
                pass
        
    except Exception as e:
        logger.error(f"Error in API search: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def _process_scrape_result(case, scrape_result):
    """Process and save scrape results to database"""
    try:
        # Update case with results
        case.response_data = json.dumps(scrape_result, default=str)
        case.status = 'success' if scrape_result.get('success') else 'failed'
        
        if scrape_result.get('success'):
            # Save case details
            parties = scrape_result.get('parties', {})
            case_detail = CaseDetail(
                case_id=case.id,
                parties_plaintiff=parties.get('plaintiff', '')[:500],
                parties_defendant=parties.get('defendant', '')[:500],
                filing_date=_parse_date(scrape_result.get('filing_date')),
                next_hearing_date=_parse_date(scrape_result.get('next_hearing')),
                case_status=scrape_result.get('status', '')[:100]
            )
            db.session.add(case_detail)
            
            # Save orders
            orders_saved = 0
            for order_data in scrape_result.get('orders', []):
                try:
                    order = Order(
                        case_id=case.id,
                        order_date=_parse_date(order_data.get('date')),
                        order_type=order_data.get('type', '')[:100],
                        pdf_url=order_data.get('pdf_url', '')[:500]
                    )
                    db.session.add(order)
                    orders_saved += 1
                except Exception as order_error:
                    logger.warning(f"Failed to save order: {order_error}")
                    continue
            
            logger.info(f"Processed case details and {orders_saved} orders")
            db.session.commit()
            return True
        else:
            db.session.commit()
            return False
            
    except Exception as e:
        logger.error(f"Error processing scrape result: {str(e)}")
        db.session.rollback()
        return False

@app.route('/test-captcha')
def test_captcha():
    """Debug endpoint to test CAPTCHA detection"""
    try:
        scraper_instance = CourtScraper()
        result = scraper_instance.test_captcha_detection()
        
        return jsonify({
            'success': result,
            'message': 'Check logs for CAPTCHA detection details'
        })
    except Exception as e:
        logger.error(f"Error testing CAPTCHA: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/retry-case/<int:case_id>')
def retry_case(case_id):
    """Retry scraping for a failed case"""
    try:
        case = Case.query.get_or_404(case_id)
        
        if case.status == 'success':
            flash('Case already has successful data', 'info')
            return redirect(url_for('case_detail', case_id=case_id))
        
        # Update status to pending
        case.status = 'pending'
        db.session.commit()
        
        # Retry scraping
        scraper_instance = CourtScraper()
        try:
            scrape_result = scraper_instance.scrape_case_data(
                case.case_type, case.case_number, case.filing_year
            )
            
            success = _process_scrape_result(case, scrape_result)
            
            if success:
                flash('Case retry successful!', 'success')
            else:
                flash(f"Retry failed: {scrape_result.get('error', 'Unknown error')}", 'error')
                
        finally:
            try:
                scraper_instance._close_driver()
            except:
                pass
        
        return redirect(url_for('case_detail', case_id=case_id))
        
    except Exception as e:
        logger.error(f"Error retrying case: {str(e)}")
        flash('Error during retry. Please try again.', 'error')
        return redirect(url_for('case_detail', case_id=case_id))

@app.route('/bulk-download/<int:case_id>')
def bulk_download_case_pdfs(case_id):
    """Download all PDFs for a case as a ZIP file"""
    try:
        import zipfile
        import tempfile
        
        case = Case.query.get_or_404(case_id)
        orders = Order.query.filter_by(case_id=case_id).all()
        
        if not orders:
            flash('No orders found for this case', 'error')
            return redirect(url_for('case_detail', case_id=case_id))
        
        # Create temporary ZIP file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                scraper_instance = CourtScraper()
                
                try:
                    for order in orders:
                        if order.pdf_url:
                            try:
                                pdf_content = scraper_instance.download_pdf(order.pdf_url)
                                if pdf_content:
                                    date_str = order.order_date.strftime('%Y-%m-%d') if order.order_date else 'unknown'
                                    filename = f"{sanitize_filename(order.order_type)}_{date_str}.pdf"
                                    zip_file.writestr(filename, pdf_content)
                                    logger.info(f"Added to ZIP: {filename}")
                            except Exception as pdf_error:
                                logger.warning(f"Failed to add PDF to ZIP: {pdf_error}")
                                continue
                finally:
                    try:
                        scraper_instance._close_driver()
                    except:
                        pass
            
            zip_filename = f"case_{sanitize_filename(case.case_number)}_orders.zip"
            return send_file(temp_zip.name, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        logger.error(f"Error creating bulk download: {str(e)}")
        flash('Error creating download. Please try individual downloads.', 'error')
        return redirect(url_for('case_detail', case_id=case_id))

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check scraper dependencies
        scraper_instance = CourtScraper()
        driver_available = scraper_instance._setup_driver()
        if driver_available:
            scraper_instance._close_driver()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'webdriver': 'available' if driver_available else 'unavailable',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Endpoint not found'}), 404
    return render_template('error.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('error.html', error='Internal server error'), 500

if __name__ == '__main__':
    # Ensure database tables exist
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
    
    # Configuration from environment
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    logger.info(f"Starting Flask app on {host}:{port} (debug={debug_mode})")
    app.run(debug=debug_mode, host=host, port=port)