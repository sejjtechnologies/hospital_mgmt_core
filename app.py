from flask import Flask, render_template
from routes.admin_routes import admin_bp
from routes.doctor_routes import doctor_bp
from routes.receptionist_routes import receptionist_bp
from routes.accountant_routes import accountant_bp
from routes.pharmacist_routes import pharmacist_bp
from routes.auth_routes import auth_bp  # ✅ Register shared login route
from datetime import datetime
import os

app = Flask(__name__)

# Load secret key from environment variable (your exact key is set in Render)
app.secret_key = os.getenv('SECRET_KEY', 's3jj$2025!secureKey!')  # ✅ Secure and fallback-safe

# Profile picture upload folder
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # Ensure folder exists

# Register Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(receptionist_bp)
app.register_blueprint(accountant_bp)
app.register_blueprint(pharmacist_bp)
app.register_blueprint(auth_bp)  # ✅ Shared login for all non-admin roles

# Custom Jinja filter for datetime formatting
@app.template_filter('datetime')
def format_datetime(value, format='%A %b %d, %Y %I:%M %p'):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(format)

# Landing Page Route
@app.route('/')
def landing():
    return render_template('landing_page.html')

# Local development only
if __name__ == '__main__':
    app.run(debug=False)  # Render uses gunicorn, so this is ignored in production