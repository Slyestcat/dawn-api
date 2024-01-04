import json
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from pyotp import TOTP
from typing import Optional
import mysql.connector

class UserCredentials(BaseModel):
    member_id: int
    mfa_details: str

# Replace these with your actual MySQL connection details
DB_CONFIG = {
    "host": "143.198.26.35",
    "user": "dawn_reader",
    "password": "*7FjA5Ao4-uEmC7P",
    "database": "dawn_web",
}

# Function to fetch the user's TOTP secret key from the database
def fetch_secret_key(member_id: int) -> UserCredentials:
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Replace 'users' with your actual table name
        query = f"SELECT member_id, mfa_details FROM core_members WHERE member_id = {member_id}"
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            return UserCredentials(**result)
        else:
            raise HTTPException(status_code=404, detail="User not found")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    finally:
        if cursor:
            cursor.close()
        if connection.is_connected():
            connection.close()

# Dependency to validate the 2FA code
def validate_totp_code(code: str, credentials: UserCredentials = Depends(fetch_secret_key)) -> bool:
    
    google_json = json.loads(credentials.mfa_details)
    google_secret_key =  google_json.get('google', '')
    
    totp = TOTP(google_secret_key)

    # Validate the code
    return totp.verify(code)