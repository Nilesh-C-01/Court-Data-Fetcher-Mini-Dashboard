"""
Database initialization script for Court Data Fetcher
Creates all necessary tables and initial data
"""

import os
import sys
from datetime import datetime
from flask import Flask
from dotenv import load_dotenv

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, Case, CaseDetail, Order
from utils import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()

def create_app():
    """Create Flask app for database initialization"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.getenv('DATABASE_PATH', 'court_data.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def init_database():
    """Initialize database with tables and sample data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Check if sample data already exists
            if Case.query.first():
                print("✓ Sample data already exists, skipping insertion")
                return
            
            # Create sample data for testing
            print("Inserting sample data...")
            
            # Sample case 1
            sample_case1 = Case(
                case_type='Civil Appeal',
                case_number='1234/2023',
                filing_year=2023,
                status='success',
                response_data='{"success": true, "sample": true}'
            )
            db.session.add(sample_case1)
            db.session.flush()  # Get the ID
            
            # Sample case detail 1
            sample_detail1 = CaseDetail(
                case_id=sample_case1.id,
                parties_plaintiff='ABC Corporation Ltd.',
                parties_defendant='XYZ Industries Pvt. Ltd.',
                filing_date=datetime(2023, 3, 15).date(),
                next_hearing_date=datetime(2024, 1, 20).date(),
                case_status='Pending'
            )
            db.session.add(sample_detail1)
            
            # Sample order 1
            sample_order1 = Order(
                case_id=sample_case1.id,
                order_date=datetime(2023, 6, 10).date(),
                order_type='Interim Order',
                pdf_url='https://example.com/order1.pdf'
            )
            db.session.add(sample_order1)
            
            # Sample case 2
            sample_case2 = Case(
                case_type='Criminal Appeal',
                case_number='5678/2022',
                filing_year=2022,
                status='success',
                response_data='{"success": true, "sample": true}'
            )
            db.session.add(sample_case2)
            db.session.flush()
            
            # Sample case detail 2
            sample_detail2 = CaseDetail(
                case_id=sample_case2.id,
                parties_plaintiff='State of Delhi',
                parties_defendant='John Doe',
                filing_date=datetime(2022, 8, 5).date(),
                next_hearing_date=datetime(2023, 12, 15).date(),
                case_status='Under Trial'
            )
            db.session.add(sample_detail2)
            
            # Sample order 2
            sample_order2 = Order(
                case_id=sample_case2.id,
                order_date=datetime(2023, 1, 25).date(),
                order_type='Judgment',
                pdf_url='https://example.com/judgment1.pdf'
            )
            db.session.add(sample_order2)
            
            # Failed case example
            failed_case = Case(
                case_type='Civil Writ Petition',
                case_number='9999/2023',
                filing_year=2023,
                status='failed',
                response_data='{"success": false, "error": "Case not found"}'
            )
            db.session.add(failed_case)
            
            # Commit all changes
            db.session.commit()
            print("✓ Sample data inserted successfully")
            
            # Display summary
            print("\nDatabase Summary:")
            print(f"Total Cases: {Case.query.count()}")
            print(f"Total Case Details: {CaseDetail.query.count()}")
            print(f"Total Orders: {Order.query.count()}")
            print(f"Successful Cases: {Case.query.filter(Case.status == 'success').count()}")
            print(f"Failed Cases: {Case.query.filter(Case.status == 'failed').count()}")
            
        except Exception as e:
            print(f"✗ Error initializing database: {str(e)}")
            db.session.rollback()
            raise

def reset_database():
    """Reset database by dropping and recreating all tables"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Resetting database...")
            db.drop_all()
            print("✓ All tables dropped")
            init_database()
            print("✓ Database reset successfully")
            
        except Exception as e:
            print(f"✗ Error resetting database: {str(e)}")
            raise

def backup_database():
    """Create a backup of the current database"""
    try:
        import shutil
        from datetime import datetime
        
        db_path = os.getenv('DATABASE_PATH', 'court_data.db')
        if not os.path.exists(db_path):
            print("✗ Database file not found")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{db_path}.backup_{timestamp}"
        
        shutil.copy2(db_path, backup_path)
        print(f"✓ Database backed up to: {backup_path}")
        
    except Exception as e:
        print(f"✗ Error creating backup: {str(e)}")

def main():
    """Main function to handle command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management for Court Data Fetcher')
    parser.add_argument('--reset', action='store_true', help='Reset database (drop and recreate)')
    parser.add_argument('--backup', action='store_true', help='Create database backup')
    parser.add_argument('--init', action='store_true', help='Initialize database (default)')
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            confirm = input("Are you sure you want to reset the database? This will delete all data. (yes/no): ")
            if confirm.lower() == 'yes':
                reset_database()
            else:
                print("Database reset cancelled")
        elif args.backup:
            backup_database()
        else:
            # Default action
            init_database()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"✗ Operation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()