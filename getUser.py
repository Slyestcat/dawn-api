import mysql.connector

def fetch_user_data(username: str):
    # Replace these with your actual MySQL connection details
    db_config = {
        "host": "143.198.26.35",
        "user": "dawn_reader",
        "password": "*7FjA5Ao4-uEmC7P",
        "database": "dawn_web",
    }

    try:
        # Connect to the MySQL server
        connection = mysql.connector.connect(**db_config)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor(dictionary=True)

        # Execute the SQL query
        cursor.execute(f"SELECT * FROM core_members WHERE name = '{username}'")

        # Fetch the result
        result = cursor.fetchone()

        return result

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()