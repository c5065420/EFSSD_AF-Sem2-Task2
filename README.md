# EFSSD_AF-Sem2-Task2
 Full Stack Software Development Task 2 – Vantage Group Project - Kickoff Connect

 ## Setup

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Initialise and seed the database:**
   ```
   python init_db.py
   ```

3. **Run the app:**
   ```
   python app.py
   ```

4. **Open in browser:**
   http://localhost:81

## Demo Login Details

- **Admin:** `admin` / `AdminPass2025!`
- **User:** `joe` / `FanPass2025!`
- **User:** `jacky` / `FanPass2025!`

## Project file structure

kickoff_connect/
├── app.py                  # Main Flask app and routes
├── init_db.py              # Database initialisation and seeding
├── requirements.txt        # Python dependencies
├── db/
│   ├── __init__.py
│   ├── db.py               # All database functions
│   └── kickoff.db          # SQLite database (created on init)
├── static/
│   ├── styles.css          # Custom CSS
│   └── uploads/            # Uploaded poster images
└── templates/
    ├── base.html           # Base template (nav, sidebar, footer)
    ├── index.html          # Home page
    ├── login.html
    ├── register.html
    ├── about.html
    ├── contact.html
    ├── trips.html          # Browse all trips
    ├── trip.html           # Trip detail + booking
    ├── create.html         # Post a new trip
    ├── update.html         # Edit a trip
    ├── bookings.html       # My bookings
    ├── mytrips.html        # Trips I've organised
    └── admin.html          # Admin panel
