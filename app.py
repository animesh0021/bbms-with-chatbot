from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dateutil.relativedelta import relativedelta

# Import the central db instance and init function
from database import db, init_db
# Import all models from models.py
from models import User, Donor, BloodInventory, BloodRequest

# Import chatbot module
try:
    import chatbot
except ImportError:
    chatbot = None
    print("Warning: chatbot.py not found. Chatbot functionality disabled.")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'blood-bank-secret-key-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bloodbank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
init_db(app)

# Authentication required decorator
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Create tables and reset database if needed (handled by init_db, but we add extra check)
with app.app_context():
    try:
        # Try to query existing tables to check if schema needs update
        db.session.query(BloodRequest).first()
    except Exception as e:
        # If there's an error, drop all tables and recreate
        print("Database schema outdated. Recreating tables...")
        db.drop_all()
        db.create_all()
        print("Database tables recreated successfully!")

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    try:
        total_donors = Donor.query.count()
        total_blood_units_result = db.session.query(db.func.sum(BloodInventory.quantity)).scalar()
        total_blood_units = total_blood_units_result if total_blood_units_result else 0
        pending_requests = BloodRequest.query.filter_by(status='Pending').count()
        low_stock = BloodInventory.query.filter(BloodInventory.quantity < 5).all()
        
        return render_template('index.html', 
                             total_donors=total_donors,
                             total_blood_units=total_blood_units,
                             pending_requests=pending_requests,
                             low_stock=low_stock)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('index.html', 
                             total_donors=0,
                             total_blood_units=0,
                             pending_requests=0,
                             low_stock=[])

# Donor Routes
@app.route('/donors')
@login_required
def donors():
    try:
        all_donors = Donor.query.order_by(Donor.created_at.desc()).all()
        return render_template('donors.html', donors=all_donors)
    except Exception as e:
        flash(f'Error loading donors: {str(e)}', 'error')
        return render_template('donors.html', donors=[])

@app.route('/add_donor', methods=['GET', 'POST'])
@login_required
def add_donor():
    if request.method == 'POST':
        try:
            last_donation = None
            if request.form['last_donation']:
                last_donation = datetime.strptime(request.form['last_donation'], '%Y-%m-%d').date()
            
            new_donor = Donor(
                name=request.form['name'],
                age=int(request.form['age']),
                gender=request.form['gender'],
                blood_type=request.form['blood_type'],
                contact=request.form['contact'],
                email=request.form.get('email', ''),
                address=request.form.get('address', ''),
                last_donation=last_donation
            )
            db.session.add(new_donor)
            db.session.commit()
            flash('Donor added successfully!', 'success')
            return redirect(url_for('donors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding donor: {str(e)}', 'error')
    
    return render_template('add_donor.html')

@app.route('/donor/<int:donor_id>')
@login_required
def view_donor(donor_id):
    try:
        donor = Donor.query.get_or_404(donor_id)
        return render_template('view_donor.html', donor=donor)
    except Exception as e:
        flash(f'Error loading donor details: {str(e)}', 'error')
        return redirect(url_for('donors'))

@app.route('/edit_donor/<int:donor_id>', methods=['GET', 'POST'])
@login_required
def edit_donor(donor_id):
    donor = Donor.query.get_or_404(donor_id)
    
    if request.method == 'POST':
        try:
            donor.name = request.form['name']
            donor.age = int(request.form['age'])
            donor.gender = request.form['gender']
            donor.blood_type = request.form['blood_type']
            donor.contact = request.form['contact']
            donor.email = request.form.get('email', '')
            donor.address = request.form.get('address', '')
            
            if request.form['last_donation']:
                donor.last_donation = datetime.strptime(request.form['last_donation'], '%Y-%m-%d').date()
            else:
                donor.last_donation = None
            
            db.session.commit()
            flash('Donor updated successfully!', 'success')
            return redirect(url_for('donors'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating donor: {str(e)}', 'error')
    
    return render_template('edit_donor.html', donor=donor)

@app.route('/delete_donor/<int:donor_id>', methods=['POST'])
@login_required
def delete_donor(donor_id):
    try:
        donor = Donor.query.get_or_404(donor_id)
        donor_name = donor.name
        db.session.delete(donor)
        db.session.commit()
        flash(f'Donor "{donor_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting donor: {str(e)}', 'error')
    
    return redirect(url_for('donors'))

# Inventory Routes
@app.route('/inventory')
@login_required
def inventory():
    try:
        inventory_items = BloodInventory.query.all()
        
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        inventory_summary = []
        
        for blood_type in blood_types:
            total_result = db.session.query(db.func.sum(BloodInventory.quantity)).filter_by(blood_type=blood_type).scalar()
            total = total_result if total_result else 0
            inventory_summary.append({
                'blood_type': blood_type,
                'total': total,
                'status': 'Low' if total < 5 else 'Adequate'
            })
        
        return render_template('inventory.html', 
                             inventory=inventory_items,
                             summary=inventory_summary)
    except Exception as e:
        flash(f'Error loading inventory: {str(e)}', 'error')
        return render_template('inventory.html', 
                             inventory=[],
                             summary=[])

@app.route('/add_inventory', methods=['POST'])
@login_required
def add_inventory():
    try:
        blood_type = request.form['blood_type']
        quantity = int(request.form['quantity'])
        location = request.form.get('location', 'Main Storage')
        
        expiry_date = datetime.now().date() + timedelta(days=42)
        
        new_inventory = BloodInventory(
            blood_type=blood_type,
            quantity=quantity,
            location=location,
            expiry_date=expiry_date
        )
        
        db.session.add(new_inventory)
        db.session.commit()
        flash('Blood units added to inventory successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding to inventory: {str(e)}', 'error')
    
    return redirect(url_for('inventory'))

@app.route('/inventory/<int:inventory_id>')
@login_required
def view_inventory(inventory_id):
    try:
        inventory_item = BloodInventory.query.get_or_404(inventory_id)
        today = date.today()
        days_left = None
        if inventory_item.expiry_date:
            days_left = (inventory_item.expiry_date - today).days
        
        return render_template('view_inventory.html', inventory=inventory_item, today=today, days_left=days_left)
    except Exception as e:
        flash(f'Error loading inventory details: {str(e)}', 'error')
        return redirect(url_for('inventory'))

@app.route('/edit_inventory/<int:inventory_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(inventory_id):
    inventory_item = BloodInventory.query.get_or_404(inventory_id)
    
    if request.method == 'POST':
        try:
            inventory_item.blood_type = request.form['blood_type']
            inventory_item.quantity = int(request.form['quantity'])
            inventory_item.location = request.form['location']
            inventory_item.status = request.form['status']
            
            if request.form['expiry_date']:
                inventory_item.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
            else:
                inventory_item.expiry_date = None
            
            db.session.commit()
            flash('Inventory item updated successfully!', 'success')
            return redirect(url_for('inventory'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating inventory: {str(e)}', 'error')
    
    return render_template('edit_inventory.html', inventory=inventory_item)

@app.route('/delete_inventory/<int:inventory_id>', methods=['POST'])
@login_required
def delete_inventory(inventory_id):
    try:
        inventory_item = BloodInventory.query.get_or_404(inventory_id)
        blood_type = inventory_item.blood_type
        db.session.delete(inventory_item)
        db.session.commit()
        flash(f'Inventory item (Blood Type: {blood_type}) deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting inventory item: {str(e)}', 'error')
    
    return redirect(url_for('inventory'))

# Blood Request Routes
@app.route('/requests')
@login_required
def blood_requests():
    try:
        all_requests = BloodRequest.query.order_by(BloodRequest.request_date.desc()).all()
        return render_template('requests.html', requests=all_requests)
    except Exception as e:
        flash(f'Error loading requests: {str(e)}', 'error')
        return render_template('requests.html', requests=[])

@app.route('/add_request', methods=['POST'])
@login_required
def add_request():
    try:
        new_request = BloodRequest(
            patient_name=request.form['patient_name'],
            hospital=request.form['hospital'],
            blood_type=request.form['blood_type'],
            units_required=int(request.form['units_required']),
            urgency=request.form['urgency'],
            contact_person=request.form['contact_person'],
            contact_number=request.form['contact_number'],
            notes=request.form.get('notes', '')
        )
        
        db.session.add(new_request)
        db.session.commit()
        flash('Blood request submitted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error submitting request: {str(e)}', 'error')
    
    return redirect(url_for('blood_requests'))

@app.route('/request/<int:request_id>')
@login_required
def view_request(request_id):
    try:
        blood_request = BloodRequest.query.get_or_404(request_id)
        return render_template('view_request.html', blood_request=blood_request)
    except Exception as e:
        flash(f'Error loading request details: {str(e)}', 'error')
        return redirect(url_for('blood_requests'))

@app.route('/edit_request/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    blood_request = BloodRequest.query.get_or_404(request_id)
    
    if request.method == 'POST':
        try:
            blood_request.patient_name = request.form['patient_name']
            blood_request.hospital = request.form['hospital']
            blood_request.blood_type = request.form['blood_type']
            blood_request.units_required = int(request.form['units_required'])
            blood_request.urgency = request.form['urgency']
            blood_request.contact_person = request.form['contact_person']
            blood_request.contact_number = request.form['contact_number']
            blood_request.notes = request.form.get('notes', '')
            
            db.session.commit()
            flash('Blood request updated successfully!', 'success')
            return redirect(url_for('blood_requests'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating request: {str(e)}', 'error')
    
    return render_template('edit_request.html', blood_request=blood_request)

@app.route('/delete_request/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    try:
        blood_request = BloodRequest.query.get_or_404(request_id)
        patient_name = blood_request.patient_name
        db.session.delete(blood_request)
        db.session.commit()
        flash(f'Blood request for "{patient_name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting request: {str(e)}', 'error')
    
    return redirect(url_for('blood_requests'))

@app.route('/update_request_status/<int:request_id>', methods=['POST'])
@login_required
def update_request_status(request_id):
    try:
        request_item = BloodRequest.query.get_or_404(request_id)
        new_status = request.form['status']
        request_item.status = new_status
        db.session.commit()
        flash(f'Request status updated to {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating request: {str(e)}', 'error')
    
    return redirect(url_for('blood_requests'))

# Reports Route
@app.route('/reports')
@login_required
def reports():
    try:
        donor_stats = db.session.query(
            Donor.blood_type,
            db.func.count(Donor.id)
        ).group_by(Donor.blood_type).all()
        
        inventory_stats = db.session.query(
            BloodInventory.blood_type,
            db.func.sum(BloodInventory.quantity)
        ).group_by(BloodInventory.blood_type).all()
        
        request_stats = db.session.query(
            BloodRequest.blood_type,
            db.func.sum(BloodRequest.units_required)
        ).group_by(BloodRequest.blood_type).all()
        
        return render_template('reports.html',
                             donor_stats=donor_stats,
                             inventory_stats=inventory_stats,
                             request_stats=request_stats)
    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return render_template('reports.html',
                             donor_stats=[],
                             inventory_stats=[],
                             request_stats=[])

# API Routes
@app.route('/api/donors_by_blood_type')
@login_required
def donors_by_blood_type():
    try:
        stats = db.session.query(
            Donor.blood_type,
            db.func.count(Donor.id)
        ).group_by(Donor.blood_type).all()
        
        return jsonify([{'blood_type': blood_type, 'count': count} for blood_type, count in stats])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chart API endpoints
@app.route('/api/charts/inventory')
@login_required
def chart_inventory():
    try:
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        values = []
        for bt in blood_types:
            total = db.session.query(db.func.sum(BloodInventory.quantity)).filter_by(blood_type=bt).scalar() or 0
            values.append(total)
        return jsonify({'labels': blood_types, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/donor_trend')
@login_required
def chart_donor_trend():
    try:
        today = date.today()
        labels = []
        values = []
        for i in range(5, -1, -1):
            month_start = today.replace(day=1) - relativedelta(months=i)
            month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
            count = Donor.query.filter(
                Donor.created_at >= month_start,
                Donor.created_at <= month_end
            ).count()
            labels.append(month_start.strftime('%b %Y'))
            values.append(count)
        return jsonify({'labels': labels, 'values': values})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/requests')
@login_required
def chart_requests():
    try:
        statuses = ['Pending', 'Fulfilled', 'Cancelled']
        counts = []
        for status in statuses:
            count = BloodRequest.query.filter_by(status=status).count()
            counts.append(count)
        return jsonify({'labels': statuses, 'values': counts})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/donor_distribution')
@login_required
def chart_donor_distribution():
    try:
        stats = db.session.query(
            Donor.blood_type,
            db.func.count(Donor.id)
        ).group_by(Donor.blood_type).all()
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        type_map = {bt: 0 for bt in blood_types}
        for bt, cnt in stats:
            type_map[bt] = cnt
        return jsonify({'labels': blood_types, 'values': [type_map[bt] for bt in blood_types]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/inventory_vs_request')
@login_required
def chart_inventory_vs_request():
    try:
        blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        inventory = []
        requests = []
        for bt in blood_types:
            inv = db.session.query(db.func.sum(BloodInventory.quantity)).filter_by(blood_type=bt).scalar() or 0
            req = db.session.query(db.func.sum(BloodRequest.units_required)).filter_by(blood_type=bt).scalar() or 0
            inventory.append(inv)
            requests.append(req)
        return jsonify({
            'labels': blood_types,
            'inventory': inventory,
            'requests': requests
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Chatbot API route
@app.route('/api/chatbot', methods=['POST'])
@login_required
def chatbot_api():
    if not chatbot:
        return jsonify({'reply': 'Chatbot module is not available.'}), 503

    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'reply': 'Missing message.'}), 400

    user_message = data['message']
    try:
        reply = chatbot.get_bot_response(user_message)
        return jsonify({'reply': reply})
    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'reply': 'Sorry, I encountered an error. Please try again later.'}), 500

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 50)
    print("Blood Bank Management System Starting...")
    print("Access the application at: http://localhost:5000")
    print("Default login: admin / admin123")
    print("Press CTRL+C to stop the server")
    print("=" * 50)
    
    # Create default admin user if not exists
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
