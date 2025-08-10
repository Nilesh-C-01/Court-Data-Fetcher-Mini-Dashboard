"""
Unit tests for Court Data Fetcher application
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Case, CaseDetail, Order

class CourtDataFetcherTestCase(unittest.TestCase):
    """Base test case for the application"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.db_fd, app.config['DATABASE'] = tempfile.mkstemp()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up test fixtures"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(app.config['DATABASE'])

class HomePageTestCase(CourtDataFetcherTestCase):
    """Test cases for home page"""
    
    def test_home_page_loads(self):
        """Test that home page loads successfully"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Court Data Fetcher', response.data)
        self.assertIn(b'Search Case Information', response.data)
    
    def test_search_form_present(self):
        """Test that search form is present on home page"""
        response = self.app.get('/')
        self.assertIn(b'case_type', response.data)
        self.assertIn(b'case_number', response.data)
        self.assertIn(b'filing_year', response.data)
        self.assertIn(b'Search Case', response.data)

class SearchTestCase(CourtDataFetcherTestCase):
    """Test cases for case search functionality"""
    
    def test_search_with_valid_data(self):
        """Test search with valid case data"""
        response = self.app.post('/search', data={
            'case_type': 'Civil Appeal',
            'case_number': '1234',
            'filing_year': '2023'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that case was created in database
        case = Case.query.filter_by(case_number='1234').first()
        self.assertIsNotNone(case)
        self.assertEqual(case.case_type, 'Civil Appeal')
        self.assertEqual(case.filing_year, 2023)
    
    def test_search_with_missing_data(self):
        """Test search with missing required data"""
        response = self.app.post('/search', data={
            'case_type': '',
            'case_number': '1234',
            'filing_year': '2023'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'All fields are required', response.data)
    
    def test_search_with_invalid_case_number(self):
        """Test search with invalid case number"""
        response = self.app.post('/search', data={
            'case_type': 'Civil Appeal',
            'case_number': 'abc123',
            'filing_year': '2023'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid case number format', response.data)
    
    def test_search_with_invalid_year(self):
        """Test search with invalid filing year"""
        response = self.app.post('/search', data={
            'case_type': 'Civil Appeal',
            'case_number': '1234',
            'filing_year': 'invalid'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid filing year', response.data)

class CaseDetailTestCase(CourtDataFetcherTestCase):
    """Test cases for case detail functionality"""
    
    def setUp(self):
        super().setUp()
        # Create a test case
        self.test_case = Case(
            case_type='Civil Appeal',
            case_number='1234/2023',
            filing_year=2023,
            status='success'
        )
        db.session.add(self.test_case)
        db.session.commit()
    
    def test_case_detail_page_loads(self):
        """Test that case detail page loads successfully"""
        response = self.app.get(f'/case/{self.test_case.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Case Details', response.data)
        self.assertIn(b'1234/2023', response.data)
    
    def test_case_detail_with_invalid_id(self):
        """Test case detail with invalid case ID"""
        response = self.app.get('/case/99999')
        self.assertEqual(response.status_code, 404)
    
    def test_case_detail_with_case_details(self):
        """Test case detail page with full case details"""
        # Add case details
        case_detail = CaseDetail(
            case_id=self.test_case.id,
            parties_plaintiff='Test Plaintiff',
            parties_defendant='Test Defendant',
            filing_date=datetime(2023, 1, 15).date(),
            case_status='Active'
        )
        db.session.add(case_detail)
        
        # Add order
        order = Order(
            case_id=self.test_case.id,
            order_date=datetime(2023, 6, 10).date(),
            order_type='Interim Order',
            pdf_url='http://example.com/order.pdf'
        )
        db.session.add(order)
        db.session.commit()
        
        response = self.app.get(f'/case/{self.test_case.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Plaintiff', response.data)
        self.assertIn(b'Test Defendant', response.data)
        self.assertIn(b'Interim Order', response.data)

class HistoryTestCase(CourtDataFetcherTestCase):
    """Test cases for search history"""
    
    def setUp(self):
        super().setUp()
        # Create test cases
        for i in range(5):
            case = Case(
                case_type='Civil Appeal',
                case_number=f'{1000 + i}/2023',
                filing_year=2023,
                status='success' if i % 2 == 0 else 'failed'
            )
            db.session.add(case)
        db.session.commit()
    
    def test_history_page_loads(self):
        """Test that history page loads successfully"""
        response = self.app.get('/history')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Search History', response.data)
    
    def test_history_shows_cases(self):
        """Test that history page shows all cases"""
        response = self.app.get('/history')
        self.assertIn(b'1000/2023', response.data)
        self.assertIn(b'1004/2023', response.data)
    
    def test_history_pagination(self):
        """Test history pagination"""
        response = self.app.get('/history?page=1')
        self.assertEqual(response.status_code, 200)

class APITestCase(CourtDataFetcherTestCase):
    """Test cases for API endpoints"""
    
    def setUp(self):
        super().setUp()
        # Create a test case
        self.test_case = Case(
            case_type='Civil Appeal',
            case_number='1234',
            filing_year=2023,
            status='success'
        )
        db.session.add(self.test_case)
        db.session.commit()
    
    def test_api_case_data_success(self):
        """Test API endpoint for case data"""
        response = self.app.get('/api/case/1234')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['case_number'], '1234')
        self.assertEqual(data['case_type'], 'Civil Appeal')
        self.assertEqual(data['filing_year'], 2023)
    
    def test_api_case_data_not_found(self):
        """Test API endpoint with non-existent case"""
        response = self.app.get('/api/case/9999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_response_format(self):
        """Test API response format"""
        response = self.app.get('/api/case/1234')
        data = json.loads(response.data)
        
        # Check required fields
        required_fields = ['case_number', 'case_type', 'filing_year', 'status', 'details', 'orders']
        for field in required_fields:
            self.assertIn(field, data)

class UtilityTestCase(CourtDataFetcherTestCase):
    """Test cases for utility functions"""
    
    def test_case_number_validation(self):
        """Test case number validation"""
        from utils import validate_case_number
        
        # Valid case numbers
        self.assertTrue(validate_case_number('1234'))
        self.assertTrue(validate_case_number('123/456'))
        self.assertTrue(validate_case_number('999-888'))
        
        # Invalid case numbers
        self.assertFalse(validate_case_number(''))
        self.assertFalse(validate_case_number('abc'))
        self.assertFalse(validate_case_number('123abc'))
        self.assertFalse(validate_case_number(None))
    
    def test_filing_year_validation(self):
        """Test filing year validation"""
        from utils import validate_filing_year
        
        # Valid years
        self.assertTrue(validate_filing_year(2023))
        self.assertTrue(validate_filing_year('2022'))
        self.assertTrue(validate_filing_year(2000))
        
        # Invalid years
        self.assertFalse(validate_filing_year(1949))
        self.assertFalse(validate_filing_year(2030))
        self.assertFalse(validate_filing_year('abc'))
        self.assertFalse(validate_filing_year(None))
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        from utils import sanitize_filename
        
        # Test various problematic characters
        self.assertEqual(sanitize_filename('file<>name'), 'file__name')
        self.assertEqual(sanitize_filename('file:name'), 'file_name')
        self.assertEqual(sanitize_filename('file/name'), 'file_name')
        self.assertEqual(sanitize_filename(''), 'file_' + datetime.now().strftime("%Y%m%d")[:-2])  # Partial match

class DatabaseTestCase(CourtDataFetcherTestCase):
    """Test cases for database models"""
    
    def test_case_model_creation(self):
        """Test Case model creation"""
        case = Case(
            case_type='Civil Appeal',
            case_number='1234/2023',
            filing_year=2023,
            status='success'
        )
        db.session.add(case)
        db.session.commit()
        
        retrieved_case = Case.query.filter_by(case_number='1234/2023').first()
        self.assertIsNotNone(retrieved_case)
        self.assertEqual(retrieved_case.case_type, 'Civil Appeal')
    
    def test_case_detail_relationship(self):
        """Test relationship between Case and CaseDetail"""
        case = Case(
            case_type='Civil Appeal',
            case_number='1234/2023',
            filing_year=2023
        )
        db.session.add(case)
        db.session.commit()
        
        case_detail = CaseDetail(
            case_id=case.id,
            parties_plaintiff='Test Plaintiff'
        )
        db.session.add(case_detail)
        db.session.commit()
        
        self.assertEqual(len(case.details), 1)
        self.assertEqual(case.details[0].parties_plaintiff, 'Test Plaintiff')
    
    def test_order_relationship(self):
        """Test relationship between Case and Order"""
        case = Case(
            case_type='Civil Appeal',
            case_number='1234/2023',
            filing_year=2023
        )
        db.session.add(case)
        db.session.commit()
        
        order = Order(
            case_id=case.id,
            order_type='Judgment',
            pdf_url='http://example.com/judgment.pdf'
        )
        db.session.add(order)
        db.session.commit()
        
        self.assertEqual(len(case.orders), 1)
        self.assertEqual(case.orders[0].order_type, 'Judgment')

if __name__ == '__main__':
    unittest.main()