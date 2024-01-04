import mysql.connector
import json

def retrieve_donation_data_for_user(username):
    donations = []

    # Replace these placeholders with your MySQL server details
    db_config = {
        "host": "143.198.26.35",
        "user": "dawn_reader",
        "password": "*7FjA5Ao4-uEmC7P",
        "database": "dawn_store",
    }

    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()

        query = "SELECT item_number, item_name, quantity, paid FROM payments WHERE player_name = %s AND claimed = 0"
        cursor.execute(query, (username,))

        for row in cursor.fetchall():
            item_number, item_name, quantity, paid = row
            store_purchase = {
                'id': item_number,
                'item_name': item_name,
                'amount': quantity,
                'quantity': 1,
                'paid': paid,
                'discount': 1
            }
            donations.append(store_purchase)

            query_update = "UPDATE payments SET claimed = 1 WHERE player_name = %s"
            cursor.execute(query_update, (username,))
            connection.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")

    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

    return donations if donations else []