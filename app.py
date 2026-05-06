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

# Trip Detail Page
@app.route('/trip/<int:id>/')
def trip(id):
    trip_data = get_trip_by_id(id)

    if trip_data:
        # Get count of seats already booked for this trip
        seats_booked = get_seats_booked_for_trip(id)
        return render_template('trip.html', title=trip_data['match_title'], trip=trip_data, seats_booked=seats_booked)
    else:
        flash(category='warning', message='Requested trip not found!')
        return redirect(url_for('trips'))


# Edit A Trip Page
@app.route('/update/<int:id>/', methods=('GET', 'POST'))
def update(id):
    trip = get_trip_by_id(id)

    # Check for errors
    error = None
    if trip is None:
        error = 'Trip not found!'
        flash(category='warning', message=error)
    elif trip['user'] != session.get('user_id'):
        error = 'You do not have permission to edit this trip.'
        flash(category='danger', message=error)
    if error:
        return redirect(url_for('trips'))

    if request.method == 'POST':
        match_title = request.form['match_title']
        competition = request.form['competition']
        match_date = request.form['match_date']
        kickoff_time = request.form['kickoff_time']
        departure_point = request.form['departure_point']
        departure_time = request.form['departure_time']
        destination = request.form['destination']
        total_seats = int(request.form['total_seats']) if request.form.get('total_seats') else 0
        price = float(request.form['price']) if request.form.get('price') else 0
        notes = request.form['notes']

        # Handle poster image upload
        poster = trip['poster']
        if 'poster' in request.files:
            poster_file = request.files['poster']
            if poster_file and poster_file.filename and poster_file.filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS:
                poster_url = f"/static/uploads/{poster_file.filename}"
                poster_file.save(f"{UPLOADS_PATH}{poster_url}")
                poster = poster_url

        if not match_title:
            flash(category='danger', message='Match title is required!')
            return redirect(url_for('update', id=id))

        update_trip(id, match_title, competition, match_date, kickoff_time,
                    departure_point, departure_time, destination, total_seats,
                    price, notes, poster)

        flash(category='success', message='Trip updated successfully!')
        return redirect(url_for('trip', id=id))
    return render_template('update.html', title="Update Trip", trip=trip)


# Delete A Trip
@app.route('/delete/<int:id>', methods=('POST',))
def delete(id):
    trip = get_trip_by_id(id)
    error = None
    if trip is None:
        error = 'Trip not found!'
        flash(category='warning', message=error)
    elif trip['user'] != session.get('user_id'):
        error = 'You do not have permission to delete this trip.'
        flash(category='danger', message=error)
    if error:
        return redirect(url_for('trips'))

    delete_trip(id)
    flash(category='success', message='Trip deleted successfully!')
    return redirect(url_for('trips'))

# Book Seats On A Trip
@app.route('/book/<int:id>', methods=('POST',))
def book(id):
    user_id = session.get('user_id')
    # Ensure user is logged in to book
    if user_id is None:
        flash(category='warning', message='You must be logged in to book seats.')
        return redirect(url_for('login'))

    # Get the trip
    trip = get_trip_by_id(id)
    if trip is None:
        flash(category='warning', message='Trip not found!')
        return redirect(url_for('trips'))

    # Get the number of seats requested
    seats = int(request.form['seats']) if request.form.get('seats') else 0

    # Validate the input
    if seats < 1:
        flash(category='danger', message='You must book at least 1 seat!')
        return redirect(url_for('trip', id=id))

    # Check there are enough seats remaining
    seats_booked = get_seats_booked_for_trip(id)
    seats_remaining = trip['total_seats'] - seats_booked
    if seats > seats_remaining:
        flash(category='danger', message=f'Sorry, only {seats_remaining} seats remaining!')
        return redirect(url_for('trip', id=id))

    # Create the booking
    create_booking(user_id, id, seats)

    # Flash a success message
    flash(category='success', message=f'Booking confirmed! {seats} seat(s) booked.')
    return redirect(url_for('myBookings'))


# My Bookings Page
@app.route('/bookings/')
def myBookings():
    user_id = session.get('user_id')
    # Ensure user is logged in
    if user_id is None:
        flash(category='warning', message='You must be logged in to view your bookings.')
        return redirect(url_for('login'))

    # Get bookings for this user
    booking_list = get_bookings_by_user(user_id)
    return render_template('bookings.html', title="My Bookings", bookings=booking_list)


# Cancel A Booking
@app.route('/cancel/<int:id>', methods=('POST',))
def cancel(id):
    user_id = session.get('user_id')
    # Ensure user is logged in
    if user_id is None:
        flash(category='warning', message='You must be logged in to cancel a booking.')
        return redirect(url_for('login'))

    # Get the booking and check ownership
    booking = get_booking_by_id(id)
    if booking is None or booking['user_id'] != user_id:
        flash(category='danger', message='Booking not found or permission denied.')
        return redirect(url_for('myBookings'))

    # Delete the booking
    delete_booking(id)
    flash(category='success', message='Booking cancelled.')
    return redirect(url_for('myBookings'))

# Run application
if __name__ == '__main__':
    print("Starting KickOff Connect...")
    print("Open Your Application in Your Browser: http://localhost:81")
    app.run(host='0.0.0.0', port=81, debug=True)
    