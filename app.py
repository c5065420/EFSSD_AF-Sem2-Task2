# This code imports the Flask library and some functions from it.
from flask import Flask, render_template, request, redirect, flash, url_for, session
import os
import requests

# Imports for the Flask-WTF
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf

# Add local database imports
from db.db import (
    init_db, get_all_trips, get_trip_by_id, create_trip, update_trip, delete_trip,
    get_trips_by_user, get_trip_count,
    get_all_users, get_user_by_id, get_user_by_username, create_user, delete_user, validate_login,
    get_all_bookings, get_bookings_by_user, get_booking_by_id, create_booking, delete_booking,
    get_seats_booked_for_trip, get_booking_count,
)

# Create a Flask application instance
app = Flask(__name__)

# Ensure database tables exist on startup
init_db()

# Allowed image extensions for uploads
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
UPLOADS_PATH = "."
os.makedirs(f"{UPLOADS_PATH}/static/uploads", exist_ok=True)


app.secret_key = 'your_secret_key'  # Required for CSRF protection
csrf = CSRFProtect(app)  # This automatically protects all POST routes
# Create the csrf_token global variable
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf())


# Global variable for site name: Used in templates to display the site name
siteName = "Kick-Off Connect"
# Set the site name in the app context
@app.context_processor
def inject_site_name():
    return dict(siteName=siteName)


# Routes Definition
#===================
# These define which template is loaded, or action is taken, depending on the URL requested
#===================
# Home Page
@app.route('/')
def index():
    fanName = "Fan"
    if 'username' in session:
        fanName = session['username']
    trips = get_all_trips(limit=6, order_by='match_date ASC')

    # Fetch upcoming World Cup fixtures from TheSportsDB
    fixtures = []
    try:
        resp = requests.get(
            'https://www.thesportsdb.com/api/v1/json/3/eventsnextleague.php?id=4429',
            timeout=3
        )
        fixtures = resp.json().get('events') or []
    except Exception:
        pass

    return render_template('index.html', title="Welcome", username=fanName, trips=trips,
                           trip_count=get_trip_count(), booking_count=get_booking_count(),
                           fixtures=fixtures)

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
        user = None
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


@app.route('/about')
def about():
    # Render the about page
    return render_template('about.html', title="About Kick-Off Connect")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # 1. Capture the data from the form
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        # 2. Process the data (For now, we'll just print it to your terminal)
        print(f"New Message from {name} ({email}): {message}")

        # 3. Add a success flash message
        flash(category='success', message="Thanks! Your message has been sent.")

        # 4. Redirect back to the contact page
        return redirect(url_for('contact'))

    # If it's a GET request, just show the page
    return render_template('contact.html', title="Contact Us")


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
            # Else, re-render the registration form with error messages
            flash(category='danger', message=f"Registration failed: {error}")
            return render_template('register.html', title="Register")

    # If the request method is GET, just render the registration form
    return render_template('register.html', title="Register")


# Trips List Page (Browse all trips)
@app.route('/trips/')
def trips():
    # Anyone can browse trips (logged in or not)
    trip_list = get_all_trips()
    # Render the trips.html template with a list of trips
    return render_template('trips.html', title="Browse Trips", trips=trip_list)


# Trip Detail Page
@app.route('/trip/<int:id>/')
def trip(id):

    # Get trip data
    trip_data = get_trip_by_id(id)

    if trip_data:
        # Get count of seats already booked for this trip
        seats_booked = get_seats_booked_for_trip(id)
        return render_template('trip.html', title=trip_data['match_title'], trip=trip_data, seats_booked=seats_booked)
    else:
        # If trip not found, redirect to trips list with a flash message
        flash(category='warning', message='Requested trip not found!')
        return redirect(url_for('trips'))


# Add A Trip Page (Organiser posts a new trip)
@app.route('/create/', methods=('GET', 'POST'))
def create():
    user = session.get('user_id')  # Get the logged-in user's ID from the session
    # Ensure user is logged in to add trips
    if user is None:
        flash(category='warning', message='You must be logged in to post a trip.')
        return redirect(url_for('login'))

    # If the request method is POST, process the form submission
    if request.method == 'POST':
        # Get the input from the form
        match_title = request.form['match_title']
        competition = request.form['competition']
        match_date = request.form['match_date']
        kickoff_time = request.form['kick-off_time']
        departure_point = request.form['departure_point']
        departure_time = request.form['departure_time']
        destination = request.form['destination']
        total_seats = int(request.form['total_seats']) if request.form.get('total_seats') else 0
        price = float(request.form['price']) if request.form.get('price') else 0
        notes = request.form['notes']

        # Handle poster image upload
        poster = None
        if 'poster' in request.files:
            poster_file = request.files['poster']
            # Check it is an image file and save it
            if poster_file and poster_file.filename and poster_file.filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS:
                # Save the file to the static/uploads directory
                poster_url = f"/static/uploads/{poster_file.filename}"
                poster_file.save(f"{UPLOADS_PATH}{poster_url}")
                poster = poster_url  # Use the uploaded file URL in database

        # Validate the input
        if not match_title:
            flash(category='danger', message='Match title is required!')
            return redirect(url_for('create'))
        if total_seats < 1:
            flash(category='danger', message='Total seats must be at least 1!')
            return redirect(url_for('create'))

        # Use the database function to insert the new trip
        create_trip(user, match_title, competition, match_date, kickoff_time,
                    departure_point, departure_time, destination, total_seats,
                    price, notes, poster)

        # Flash a success message
        flash(category='success', message='Trip posted successfully!')
        return redirect(url_for('trips'))
    return render_template('create.html', title="Post a Trip")


# Edit A Trip Page
@app.route('/update/<int:id>/', methods=('GET', 'POST'))
def update(id):
    # Get trip data
    trip = get_trip_by_id(id)

    # Check for errors
    error = None
    if trip is None:  # If trip not found, add error message
        error = 'Trip not found!'
        flash(category='warning', message=error)
    elif trip['user'] != session.get('user_id'):  # Check user is only accessing their own trips
        error = 'You do not have permission to edit this trip.'
        flash(category='danger', message=error)
    # If there was an error, redirect to trips list
    if error:
        return redirect(url_for('trips'))

    # If the request method is POST, process the form submission
    if request.method == 'POST':
        # Get the input from the form
        match_title = request.form['match_title']
        competition = request.form['competition']
        match_date = request.form['match_date']
        kickoff_time = request.form['kick-off_time']
        departure_point = request.form['departure_point']
        departure_time = request.form['departure_time']
        destination = request.form['destination']
        total_seats = int(request.form['total_seats']) if request.form.get('total_seats') else 0
        price = float(request.form['price']) if request.form.get('price') else 0
        notes = request.form['notes']

        # Handle poster image upload
        poster = trip['poster']  # Default to existing poster
        if 'poster' in request.files:
            poster_file = request.files['poster']
            # Check it is an image file and save it
            if poster_file and poster_file.filename and poster_file.filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS:
                # Save the file to the static/uploads directory
                poster_url = f"/static/uploads/{poster_file.filename}"
                poster_file.save(f"{UPLOADS_PATH}{poster_url}")
                poster = poster_url  # Use the uploaded file URL in database

        # Validate the input
        if not match_title:
            flash(category='danger', message='Match title is required!')
            return redirect(url_for('update', id=id))

        # Use the database function to update the trip
        update_trip(id, match_title, competition, match_date, kickoff_time,
                    departure_point, departure_time, destination, total_seats,
                    price, notes, poster)

        # Flash a success message and redirect to the trip page
        flash(category='success', message='Trip updated successfully!')
        return redirect(url_for('trip', id=id))
    return render_template('update.html', title="Update Trip", trip=trip)


# Delete A Trip
@app.route('/delete/<int:id>', methods=('POST',))
def delete(id):
    # Get the trip
    trip = get_trip_by_id(id)
    # Check for errors
    error = None
    if trip is None:  # If trip not found, add error message
        error = 'Trip not found!'
        flash(category='warning', message=error)
    # Check user is the owner OR is an admin
    elif trip['user'] != session.get('user_id') and not session.get('is_admin'):
        error = 'You do not have permission to delete this trip.'
        flash(category='danger', message=error)
    # If there was an error, redirect to trips list
    if error:
        return redirect(url_for('trips'))
    # Use the database function to delete the trip
    delete_trip(id)

    # Flash a success message and redirect to the trips page
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


# My Trips Page (trips this user has organised)
@app.route('/mytrips/')
def myTrips():
    user_id = session.get('user_id')
    # Ensure user is logged in
    if user_id is None:
        flash(category='warning', message='You must be logged in to view your trips.')
        return redirect(url_for('login'))

    # Get trips organised by this user
    trip_list = get_trips_by_user(user_id)
    return render_template('mytrips.html', title="My Trips", trips=trip_list)


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
    
# My Trips Page (trips this user has organised)
@app.route('/mytrips/')
def myTrips():
    user_id = session.get('user_id')
    # Ensure user is logged in
    if user_id is None:
        flash(category='warning', message='You must be logged in to view your trips.')
        return redirect(url_for('login'))

    # Get trips organised by this user
    trip_list = get_trips_by_user(user_id)
    return render_template('mytrips.html', title="My Trips", trips=trip_list)
# Run application
#=========================================================
# This code executes when the script is run directly.
if __name__ == '__main__':
    print("Starting Kick-Off Connect...")
    print("Open Your Application in Your Browser: http://localhost:81")
    # The app will run on port 81, accessible from any local IP address
    app.run(host='0.0.0.0', port=81, debug=True)
