from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Medicine(db.Model):
    __tablename__ = 'medicine'
    id = db.Column(db.Integer, primary_key=True)
    batch_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True)
    manufacturer = db.Column(db.String(100), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    mrp = db.Column(db.Float, nullable=False)
    pkg_size = db.Column(db.String(50), nullable=True)  # New column added here
