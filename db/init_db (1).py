# Initialise the database and seed with sample data.
# Run this once before starting the app: python init_db.py

from db.db import init_db, create_user, create_trip, create_booking, get_user_by_username


def seed():
    """Create the database tables and seed with sample users, trips and bookings."""
    print("Creating database tables...")
    init_db()

    # Only seed if the admin user doesn't already exist
    if get_user_by_username('admin'):
        print("Database already seeded — skipping.")
        return

    print("Creating sample users...")
    # Admin user
    create_user('admin', 'AdminPass2025!', is_admin=1)
    # Standard fan users
    create_user('jamie', 'FanPass2025!')
    create_user('sarah', 'FanPass2025!')
    create_user('tobi_a', 'FanPass2025!')
    create_user('tobi_o', 'FanPass2025!')

    # Get user IDs
    jamie = get_user_by_username('jamie')['id']
    sarah = get_user_by_username('sarah')['id']
    tobi_a = get_user_by_username('tobi_a')['id']

    print("Creating sample trips...")
    create_trip(jamie, 'Sheffield Utd vs Arsenal', 'Premier League',
                '2026-05-03', '15:00',
                'Sheffield City Centre, Pond Street Bus Station',
                '12:30', 'Bramall Lane, Sheffield', 40, 12.00,
                'Coach leaves sharp at 12:30. Return after final whistle.', None)

    create_trip(sarah, 'Leeds Utd vs Burnley', 'Championship',
                '2026-05-04', '14:00',
                'Leeds Bus Station',
                '11:00', 'Elland Road, Leeds', 40, 9.00,
                'Please bring exact change. Card payment available.', None)

    create_trip(tobi_a, 'Everton vs Spurs', 'Premier League',
                '2026-05-17', '15:00',
                'Liverpool Lime Street',
                '11:30', 'Goodison Park, Liverpool', 40, 14.00,
                'Meet at the front entrance of Lime Street.', None)

    print("Creating sample bookings...")
    create_booking(sarah, 1, 2)
    create_booking(tobi_a, 1, 1)
    create_booking(jamie, 3, 1)

    print("Done! Database seeded successfully.")
    print("\n--- Login Details ---")
    print("Admin:  admin / AdminPass2025!")
    print("User:   jamie / FanPass2025!")
    print("---------------------\n")


if __name__ == '__main__':
    seed()