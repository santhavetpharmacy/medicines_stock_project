from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from flask import Flask, render_template, request

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with something secure!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CSRF protection and Database
csrf = CSRFProtect(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define Model (Medicine)
class Medicine(db.Model):
    __tablename__ = 'medicine'
    id = db.Column(db.Integer, primary_key=True)
    purchase_date = db.Column(db.Date, nullable=False)
    batch_number = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True)
    manufacturer = db.Column(db.String(100), nullable=False)
    pkg_size = db.Column(db.String(50), nullable=True)
    expiry_date = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    supplier_name = db.Column(db.String(100), nullable=False)
    mrp = db.Column(db.Float, nullable=False)

# Home/Search Route
@app.route('/', methods=['GET', 'POST'])
def search():
    # Calculate the expiry threshold (for highlighting near-expiry medicines)
    expiry_threshold = datetime.now(timezone.utc).date() + timedelta(days=90)
    
    # Get the current local date/time in 12-hour format (with AM/PM)
    current_datetime = datetime.now()
    current_date_time = current_datetime.strftime("%A, %d %B %Y, %I:%M %p")

    # Set the location (city, state, country) as required.
    location_city = "Orathanadu, Tamil Nadu, India"

    # For live weather, this is a placeholder that you can replace with API data.
    live_weather = "Partly Cloudy, 31°C"  # Replace with dynamic data if needed.

    # Check if a medicine search term is provided.
    medicine_name = request.args.get('medicine_name')
    if medicine_name:
        search_input = medicine_name.strip()
        # If one character entered, search only at the beginning.
        if len(search_input) == 1:
            pattern = f"{search_input}%"
        else:
            pattern = f"%{search_input}%"
        results = Medicine.query.filter(Medicine.name.ilike(pattern)).all()
        return render_template('results.html', 
                               medicines=results, 
                               search_term=medicine_name,
                               expiry_threshold=expiry_threshold,
                               current_date_time=current_date_time,
                               live_weather=live_weather,
                               location_city=location_city)

    else:
        # When no search term is provided, query for all medicines expiring within the next 90 days.
        expiring_medicines = Medicine.query.filter(Medicine.expiry_date <= expiry_threshold)\
                                             .order_by(Medicine.expiry_date.asc()).all()   
        # Render the search form including the header info.
        return render_template('search.html',
                           expiry_threshold=expiry_threshold,
                           current_date_time=current_date_time,
                           live_weather=live_weather,
                           location_city=location_city,
                           expiring_medicines=expiring_medicines)

# Delete Medicine Route
@app.route('/delete/<int:id>', methods=['POST'])
def delete_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    try:
        db.session.delete(medicine)
        db.session.commit()
        flash("Medicine deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting medicine: {e}", "danger")
    return redirect(url_for('search'))

# Alphabetical Search Route
@app.route('/alphabet/<letter>')
def alphabet_filter(letter):
    letter = letter.upper()
    medicines = Medicine.query.filter(Medicine.name.ilike(letter + '%')).all()
    expiry_threshold = datetime.utcnow().date() + timedelta(days=7)
    return render_template('results.html', medicines=medicines, search_term=letter, expiry_threshold=expiry_threshold)

# Results Route
@app.route('/results')
def results():
    medicines = Medicine.query.all()
    expiry_threshold = datetime.utcnow().date() + timedelta(days=7)
    return render_template('results.html', medicines=medicines, expiry_threshold=expiry_threshold)

# Add Medicine Route
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        # Extract form data
        medicine_name = request.form.get('medicine_name').strip()
        batch_number = request.form.get('batch_number').strip()
        purchase_date_str = request.form.get('purchase_date')
        pkg_size = request.form.get('pkg_size').strip() if request.form.get('pkg_size') else None
        quantity = int(request.form.get('quantity')) if request.form.get('quantity') else 0
        expiry_date_str = request.form.get('expiry_date')
        mrp = float(request.form.get('mrp'))
        # You can have a manufacturer and supplier field in this form; otherwise, set defaults.
        manufacturer = request.form.get('manufacturer', "Unknown")
        supplier_name = request.form.get('supplier_name', "Default Supplier")
        
        try:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception as e:
            flash(f"Date conversion error: {e}", "danger")
            return redirect(url_for('add_medicine'))
            
        new_medicine = Medicine(
            name=medicine_name,
            batch_number=batch_number,
            purchase_date=purchase_date,
            pkg_size=pkg_size,
            quantity=quantity,
            expiry_date=expiry_date,
            mrp=mrp,
            manufacturer=manufacturer,
            supplier_name=supplier_name
        )
        try:
            db.session.add(new_medicine)
            db.session.commit()
            flash("Medicine added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding medicine: {e}", "danger")
        return redirect(url_for('search'))
    return render_template('add_medicine.html')

# Edit Medicine Route
@app.route('/edit_medicine/<int:id>', methods=['GET', 'POST'])
def edit_medicine(id):
    medicine = Medicine.query.get_or_404(id)
    if request.method == 'POST':
        medicine.name = request.form.get('medicine_name').strip()
        medicine.batch_number = request.form.get('batch_number').strip()
        purchase_date_str = request.form.get('purchase_date')
        medicine.pkg_size = request.form.get('pkg_size').strip() if request.form.get('pkg_size') else None
        medicine.quantity = int(request.form.get('quantity'))
        expiry_date_str = request.form.get('expiry_date')
        medicine.mrp = float(request.form.get('mrp'))
        # Update manufacturer and supplier information if provided
        medicine.manufacturer = request.form.get('manufacturer', medicine.manufacturer)
        medicine.supplier_name = request.form.get('supplier_name', medicine.supplier_name)
        try:
            medicine.purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            medicine.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception as e:
            flash(f"Error parsing dates: {e}", "danger")
            return redirect(url_for('edit_medicine', id=id))
        try:
            db.session.commit()
            flash("Medicine updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating medicine: {e}", "danger")
        return redirect(url_for('search'))
    return render_template('edit_medicine.html', medicine=medicine)

@app.route('/add_supplier_medicine', methods=['GET', 'POST'])
def add_supplier_medicine():
    if request.method == 'POST':
        # Retrieve form data
        supplier_name = request.form.get('supplier_name').strip()
        medicine_name = request.form.get('medicine_name').strip()
        batch_number = request.form.get('batch_number').strip()
        purchase_date_str = request.form.get('purchase_date')
        pkg_size = request.form.get('pkg_size').strip() if request.form.get('pkg_size') else None
        quantity = int(request.form.get('quantity')) if request.form.get('quantity') else 0
        expiry_date_str = request.form.get('expiry_date')
        mrp = float(request.form.get('mrp'))
        manufacturer = request.form.get('manufacturer', "Unknown").strip()
        
        # Convert dates from string to date objects
        try:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
            expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
        except Exception as e:
            flash(f"Date conversion error: {e}", "danger")
            return redirect(url_for('add_supplier_medicine'))
            
        # Create a new medicine record
        new_medicine = Medicine(
            name=medicine_name,
            batch_number=batch_number,
            purchase_date=purchase_date,
            pkg_size=pkg_size,
            quantity=quantity,
            expiry_date=expiry_date,
            mrp=mrp,
            manufacturer=manufacturer,
            supplier_name=supplier_name
        )
        try:
            db.session.add(new_medicine)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding supplier-based medicine: {e}", "danger")
            return redirect(url_for('add_supplier_medicine'))
        
        # Decide where to go next based on the submit action
        action = request.form.get("action")
        if action == "save_add_another":
            flash("Medicine added! You can add another product.", "success")
            # Optionally, you can pre-populate the supplier name and purchase date
            # by passing them as query parameters or storing in the session.
            return redirect(url_for('add_supplier_medicine'))
        else:
            flash("Supplier-based medicine added successfully!", "success")
            return redirect(url_for('search'))
            
    return render_template('supplier_add_medicine.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates tables if they don't exist
    app.run(debug=True)
