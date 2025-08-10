"""
Database models for Court Data Fetcher application
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Case(db.Model):
    """Model for storing case search information"""
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(100), nullable=False)
    case_number = db.Column(db.String(100), nullable=False)
    filing_year = db.Column(db.Integer, nullable=False)
    search_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_data = db.Column(db.Text)  # JSON string of scraped data
    status = db.Column(db.String(50), default='pending')  # pending, success, failed
    
    # Relationships
    details = db.relationship('CaseDetail', backref='case', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='case', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Case {self.case_number}/{self.filing_year}>'
    
    def to_dict(self):
        """Convert case to dictionary"""
        return {
            'id': self.id,
            'case_type': self.case_type,
            'case_number': self.case_number,
            'filing_year': self.filing_year,
            'search_timestamp': self.search_timestamp.isoformat() if self.search_timestamp else None,
            'status': self.status
        }

class CaseDetail(db.Model):
    """Model for storing detailed case information"""
    __tablename__ = 'case_details'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    parties_plaintiff = db.Column(db.Text)
    parties_defendant = db.Column(db.Text)
    filing_date = db.Column(db.Date)
    next_hearing_date = db.Column(db.Date)
    case_status = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<CaseDetail for Case {self.case_id}>'
    
    def to_dict(self):
        """Convert case detail to dictionary"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'parties_plaintiff': self.parties_plaintiff,
            'parties_defendant': self.parties_defendant,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'next_hearing_date': self.next_hearing_date.isoformat() if self.next_hearing_date else None,
            'case_status': self.case_status
        }

class Order(db.Model):
    """Model for storing order/judgment information"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('cases.id'), nullable=False)
    order_date = db.Column(db.Date)
    order_type = db.Column(db.String(100))  # judgment, order, notice, etc.
    pdf_url = db.Column(db.Text)
    local_pdf_path = db.Column(db.Text)  # Path to downloaded PDF
    
    def __repr__(self):
        return f'<Order {self.order_type} for Case {self.case_id}>'
    
    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'order_type': self.order_type,
            'pdf_url': self.pdf_url,
            'local_pdf_path': self.local_pdf_path
        }