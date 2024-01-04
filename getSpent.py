import mysql.connector

def fetch_and_calculate_paid(player_name):
    # MySQL database connection configuration
    db_config = {
        "host": "143.198.26.35",
        "user": "dawn_reader",
        "password": "*7FjA5Ao4-uEmC7P",
        "database": "dawn_store",
    }

    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**db_config)

        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Fetch all rows based on the player name and status "complete"
        query = f"SELECT * FROM payments WHERE player_name = '{player_name}' AND status = 'complete'"
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print(f"No 'complete' rows found for player: {player_name}")
            return 0

        # Calculate the sum of the 'paid' column for 'complete' rows
        total_paid = sum(row[4] for row in rows)  # Assuming 'paid' column is at index 4

        print(f"Total paid for {player_name} with status 'complete': {total_paid}")

        return total_paid

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return err

    finally:
        # Close the database connection
        if connection.is_connected():
            cursor.close()
            connection.close()

