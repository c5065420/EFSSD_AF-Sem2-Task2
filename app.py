# KickOff Connect - Phase 3
# Adds user authentication: registration, login, and logout.

from flask import Flask, render_template, request, redirect, flash, url_for, session

# Imports for the Flask-WTF (CSRF protection)
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Add local database imports
from db.db import *

# Create a Flask application instance
app = Flask(__name__)

# Required for CSRF protection and session signing
app.secret_key = 'your_secret_key'
csrf = CSRFProtect(app)

# Make csrf_token available in every template
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())

# Global variable for site name: Used in templates
siteName = "KickOff Connect"

@app.context_processor
def inject_site_name():
    return dict(siteName=siteName)


# Routes Definition
#===================
# Home Page
@app.route('/')
def index():
    fanName = "Fan"
    # If a 'username' exists in the session data, use this instead
    if 'username' in session:
        fanName = session['username']
    return render_template('index.html', title="Welcome", username=fanName)


# Login Page
@app.route('/login', methods=('GET', 'POST'))
def login():

    # If the request method is POST, process the login form
    if request.method == 'POST':

        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']

        # Simple validation checks
        error = None
        if not username:
            error = 'Username is required!'
        elif not password:
            error = 'Password is required!'

        # Validate user credentials
        if error is None:
            user = validate_login(username, password)
        if user is None:
            error = 'Invalid username or password!'
        else:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']

        # Display appropriate flash messages
        if error is None:
            flash(category='success', message=f"Login successful! Welcome back {username}!")
            return redirect(url_for('index'))
        else:
            flash(category='danger', message=f"Login failed: {error}")

    # If the request method is GET, render the login form
    return render_template('login.html', title="Log In")


# Register Page
@app.route('/register/', methods=('GET', 'POST'))
def register():

    # If the request method is POST, process the form submission
    if request.method == 'POST':

        # Get the username and password from the form
        username = request.form['username']
        password = request.form['password']
        repassword = request.form['repassword']

        # Simple validation checks
        error = None
        if not username:
            error = 'Username is required!'
        elif not password or not repassword:
            error = 'Password is required!'
        elif password != repassword:
            error = 'Passwords do not match!'

        # Check if username already exists
        if error is None and get_user_by_username(username):
            error = 'Username already exists! Please choose a different one.'

        # If no errors, insert the new user
        if error is None:
            create_user(username, password)
            flash(category='success', message=f"Registration successful! Welcome {username}!")
            return redirect(url_for('login'))
        else:
            flash(category='danger', message=f"Registration failed: {error}")
            return render_template('register.html', title="Register")

    return render_template('register.html', title="Register")


# Logout
@app.route('/logout/')
def logout():
    session.clear()
    flash(category='info', message='You have been logged out.')
    return redirect(url_for('index'))


# Run application
if __name__ == '__main__':
    print("Starting KickOff Connect...")
    print("Open Your Application in Your Browser: http://localhost:81")
    app.run(host='0.0.0.0', port=81, debug=True)