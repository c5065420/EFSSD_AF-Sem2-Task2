# Database module for KickOff Connect
# Handles all SQLite operations for users, trips, and bookings.

import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

# Path to the SQLite database file
DATABASE = 'db/kickoff.db'


def get_db():
    """Open a new database connection and return it."""
    conn = sqlite3.connect(DATABASE)
    # Allow rows to be accessed by column name (like a dictionary)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the database tables if they don't already exist."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Trips table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user INTEGER NOT NULL,
            match_title TEXT NOT NULL,
            competition TEXT,
            match_date TEXT,
            "kick-off_time" TEXT,
            departure_point TEXT,
            departure_time TEXT,
            destination TEXT,
            total_seats INTEGER NOT NULL,
            price REAL NOT NULL,
            notes TEXT,
            poster TEXT,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user) REFERENCES users(id)
        )
    ''')

    # Bookings table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trip_id INTEGER NOT NULL,
            seats INTEGER NOT NULL,
            created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (trip_id) REFERENCES trips(id)
        )
    ''')

    conn.commit()
    conn.close()


# ── USER FUNCTIONS ─────────────────────────────────────

def create_user(username, password, is_admin=0):
    """Insert a new user with a hashed password."""
    conn = get_db()
    cur = conn.cursor()
    hashed = generate_password_hash(password)
    cur.execute(
        'INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
        (username, hashed, is_admin)
    )
    conn.commit()
    conn.close()


def get_user_by_id(user_id):
    """Get a user record by id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cur.fetchone()
    conn.close()
    return user


def get_user_by_username(username):
    """Get a user record by username."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cur.fetchone()
    conn.close()
    return user


def get_all_users():
    """Get a list of all registered users."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users ORDER BY created DESC')
    users = cur.fetchall()
    conn.close()
    return users


def validate_login(username, password):
    """Check username and password. Return user dict if valid, else None."""
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        return user
    return None


def delete_user(user_id):
    """Delete a user and all their trips and bookings."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM bookings WHERE user_id = ?', (user_id,))
    cur.execute('DELETE FROM trips WHERE user = ?', (user_id,))
    cur.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_trip_count():
    """Return the total number of trips."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) AS count FROM trips')
    row = cur.fetchone()
    conn.close()
    return row['count']


def get_booking_count():
    """Return the total number of individual booking records."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) AS count FROM bookings')
    row = cur.fetchone()
    conn.close()
    return row['count']


# ── TRIP FUNCTIONS ─────────────────────────────────────

def create_trip(user, match_title, competition, match_date, kickoff_time,
                departure_point, departure_time, destination, total_seats,
                price, notes, poster):
    """Insert a new trip into the database."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO trips (user, match_title, competition, match_date, "kick-off_time",
                           departure_point, departure_time, destination,
                           total_seats, price, notes, poster)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user, match_title, competition, match_date, kickoff_time,
          departure_point, departure_time, destination,
          total_seats, price, notes, poster))
    conn.commit()
    conn.close()


def update_trip(trip_id, match_title, competition, match_date, kickoff_time,
                departure_point, departure_time, destination, total_seats,
                price, notes, poster):
    """Update an existing trip."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        UPDATE trips
        SET match_title=?, competition=?, match_date=?, "kick-off_time"=?,
            departure_point=?, departure_time=?, destination=?,
            total_seats=?, price=?, notes=?, poster=?
        WHERE id=?
    ''', (match_title, competition, match_date, kickoff_time,
          departure_point, departure_time, destination,
          total_seats, price, notes, poster, trip_id))
    conn.commit()
    conn.close()


def delete_trip(trip_id):
    """Delete a trip and all its associated bookings."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM bookings WHERE trip_id = ?', (trip_id,))
    cur.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
    conn.commit()
    conn.close()


def get_trip_by_id(trip_id):
    """Get a single trip by id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
    trip = cur.fetchone()
    conn.close()
    return trip


def get_all_trips(limit=None, order_by='created DESC'):
    """Get all trips, optionally limited and ordered."""
    conn = get_db()
    cur = conn.cursor()
    query = f'SELECT * FROM trips ORDER BY {order_by}'
    if limit:
        query += f' LIMIT {limit}'
    cur.execute(query)
    trips = cur.fetchall()
    conn.close()
    return trips


def get_trips_by_user(user_id):
    """Get all trips organised by a particular user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM trips WHERE user = ? ORDER BY match_date ASC', (user_id,))
    trips = cur.fetchall()
    conn.close()
    return trips


# ── BOOKING FUNCTIONS ──────────────────────────────────

def create_booking(user_id, trip_id, seats):
    """Insert a new booking."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO bookings (user_id, trip_id, seats) VALUES (?, ?, ?)',
        (user_id, trip_id, seats)
    )
    conn.commit()
    conn.close()


def get_booking_by_id(booking_id):
    """Get a single booking by id."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,))
    booking = cur.fetchone()
    conn.close()
    return booking


def get_bookings_by_user(user_id):
    """Get all bookings for a user, joined with trip info."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT b.id, b.seats, b.created,
               t.id AS trip_id, t.match_title, t.competition, t.match_date,
               t."kick-off_time", t.departure_point, t.destination, t.price, t.user AS organiser
        FROM bookings b
        JOIN trips t ON b.trip_id = t.id
        WHERE b.user_id = ?
        ORDER BY t.match_date ASC
    ''', (user_id,))
    bookings = cur.fetchall()
    conn.close()
    return bookings


def get_bookings_for_trip(trip_id):
    """Get all bookings for a particular trip (passenger list)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT b.id, b.seats, b.created, u.username, u.id AS user_id
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        WHERE b.trip_id = ?
        ORDER BY b.created ASC
    ''', (trip_id,))
    bookings = cur.fetchall()
    conn.close()
    return bookings


def get_seats_booked_for_trip(trip_id):
    """Return the total number of seats already booked on a trip."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT SUM(seats) AS total FROM bookings WHERE trip_id = ?', (trip_id,))
    row = cur.fetchone()
    conn.close()
    # Handle None when no bookings yet exist
    return row['total'] if row['total'] else 0


def get_all_bookings():
    """Get all bookings across the platform (for admin)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT b.id, b.seats, b.created, u.username,
               t.match_title, t.match_date
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN trips t ON b.trip_id = t.id
        ORDER BY b.created DESC
    ''')
    bookings = cur.fetchall()
    conn.close()
    return bookings


def delete_booking(booking_id):
    """Delete a booking."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()
