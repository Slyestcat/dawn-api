import mysql.connector

def count_unclaimed_votes(username):
    db_config = {
        "host": "143.198.26.35",
        "user": "dawn_reader",
        "password": "*7FjA5Ao4-uEmC7P",
        "database": "dawn_vote",
    }
    try:
        # Establish a connection to the MySQL database
        
        connection = mysql.connector.connect(**db_config)
        # Create a cursor to execute SQL queries
        cursor = connection.cursor()

        # Execute the SQL query to count rows where claimed is 0 for a specific username
        query = "SELECT COUNT(*) FROM votes WHERE username = %s AND claimed = 0"
        cursor.execute(query, (username,))

        # Fetch the result
        result = cursor.fetchone()

         # Execute the SQL query to update claimed status for a specific username
        update_query = "UPDATE votes SET claimed = 1 WHERE username = %s AND claimed = 0"
        cursor.execute(update_query, (username,))
        # Commit the changes to the database
        connection.commit()
        
        # Close the cursor and connection
        cursor.close()
        connection.close()

        # Return the count
        return result[0] if result else 0

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
