from flask import Flask, jsonify, render_template, request, redirect, send_file, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from flask import send_file

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Set the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profiles.db'
db = SQLAlchemy(app)

# Define the User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    pdf_path = db.Column(db.String(255), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    owner = db.Column(db.String(80), nullable=False)

# Check if the database file exists, and if not, create it.
if not os.path.exists('profiles.db'):
    with app.app_context():
        db.create_all()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    if request.method == 'POST':
        title = request.form['title']
        pdf = request.files['pdf']

        # Save the uploaded PDF file
        pdf_path = f"uploads/{title}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
        pdf.save(pdf_path)

        # Get the owner from the session
        owner = session.get('username')

        # Create a new project
        new_project = Project(title=title, pdf_path=pdf_path, owner=owner)
        db.session.add(new_project)
        db.session.commit()

        return redirect(url_for('dashboard'))

    return render_template('createProject.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            # Return an error message to the client if login fails
            return jsonify({"error": "Incorrect username or password"}), 401

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if len(username) < 6:
            return "Username must be at least 6 characters."

        # Password validation for length and content
        if len(password) < 8:
            return "Password must be at least 8 characters."

        if not any(c.isdigit() for c in password):
            return "Password must contain at least 1 number."

        if not any(c in "!@#$%^&*" for c in password):
            return "Password must contain at least 1 symbol (!@#$%^&*)."
        
        # Email validation
        if not email:
            return "Email is required."
        
        if not any(c in "@" for c in email):
            return "Email must contain @."

        # Check if the username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                return jsonify({"error": "Username already exists."}), 409
            elif existing_user.email == email:
                return jsonify({"error": "Email already exists."}), 409

        new_user = User(username=username, password=generate_password_hash(password), email=email)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Registration successful."})

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return render_template('dashboard.html', user_email=user.email)
    else:
        return redirect(url_for('login'))
    
@app.route('/profile')
def profile():
    if 'username' in session:
        user = User.query.filter_by(username=session['username']).first()
        return render_template('profile.html', user_email=user.email)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/logo')
def logo():
    return send_file('sources/pfw.png', mimetype='image/gif')

@app.route('/view_projects')
def view_projects():
    if 'username' in session:
        projects = Project.query.all()
        return render_template('view_projects.html', projects=projects)
    else:
        return redirect(url_for('login'))
    
@app.route('/view_pdf/<int:project_id>')
def view_pdf(project_id):
    project = Project.query.get_or_404(project_id)
    return send_file(project.pdf_path, as_attachment=False)

if __name__ == '__main__':
    app.run(debug=True)
