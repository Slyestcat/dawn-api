import mysql.connector

def update_world_info(world_id, name, address, uptime, activity, playerCount, playersOnline, flags, location):
    # Replace the following with your MySQL database credentials and connection details
    db_config = {
        "host": "143.198.26.35",
        "user": "dawn_reader",
        "password": "*7FjA5Ao4-uEmC7P",
        "database": "dawn_web",
    }

    separator = ", "
    playersOnline_result = separator.join(playersOnline)
    flags_result = separator.join(flags)

    try:
        # Connect to the MySQL server
        connection = mysql.connector.connect(**db_config)

        # Create a cursor object to execute SQL queries
        cursor = connection.cursor()

        # Upsert the world information in the database
        upsert_query = (
            "INSERT INTO worlds (id, name, address, uptime, activity, playerCount, "
            "playersOnline, flags, location) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE "
            "name = VALUES(name), address = VALUES(address), uptime = VALUES(uptime), "
            "activity = VALUES(activity), playerCount = VALUES(playerCount), "
            "playersOnline = VALUES(playersOnline), flags = VALUES(flags), location = VALUES(location)"
        )
        upsert_data = (world_id, name, address, uptime, activity, playerCount, playersOnline_result, flags_result, location)

        cursor.execute(upsert_query, upsert_data)

        # Commit the changes to the database
        connection.commit()

        print("World information updated successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        # Close the cursor and connection
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()