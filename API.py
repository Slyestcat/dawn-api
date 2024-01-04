from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse, PlainTextResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from claimDonation import retrieve_donation_data_for_user
from claimVote import count_unclaimed_votes
from getSpent import fetch_and_calculate_paid

from updateWorld import update_world_info
from getUser import fetch_user_data
from validateTOTP import fetch_secret_key, validate_totp_code

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 262800


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": True,
    },
    "sly": {
        "username": "sly",
        "full_name": "Sly",
        "email": "sly@dawnps.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str

class World(BaseModel):
    id: int
    name: str
    address: str
    uptime: int
    activity: str
    playerCount: int
    playersOnline: list[str] = []
    flags: list[str] = []
    location: str
    


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.post("/ping")
async def ping_pong( 
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_agent: Annotated[str | None, Header()] = None
):
    return PlainTextResponse("pong")

@app.post("/worldinfo/world/update")
async def worldinfo_world_update( 
    world: World,
    current_user: Annotated[User, Depends(get_current_active_user)],
    user_agent: Annotated[str | None, Header()] = None
):
    update_world_info(
        world_id=world.id,
        name=world.name,
        address=world.address,
        uptime=world.uptime,
        activity=world.activity,
        playerCount=world.playerCount,
        playersOnline=world.playersOnline,
        flags=world.flags,
        location=world.location
    )

    return PlainTextResponse("World information updated")

class AccountInformationRequestResults(BaseModel):
    # Define the structure of the response data
    joined: int
    member_id: int
    msg_count_new: int
    members_pass_hash: str
    mfa_details: Optional[str] = "disabled"

    def prepend_enabled_to_mfa_details(self):
        if self.mfa_details is not None:
            return "enabled"
        else:
            return "disabled"

@app.get("/user/columns/{username}")
async def get_account_information(username: str):
    # Fetch data from MySQL database
    db_data = fetch_user_data(username)

    if not db_data:
        # Return appropriate response if user not found
        return {"error": "User not found"}
    if db_data is None:
        # Return a 404 Not Found response if user not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Create an instance of AccountInformationRequestResults using Pydantic
    response_data = AccountInformationRequestResults(**db_data)

    response_data.mfa_details = response_data.prepend_enabled_to_mfa_details()

    print(response_data)

    return response_data


# API endpoint to validate the 2FA code
@app.get("/user/{member_id}/check2fa")
async def check_2fa_code(member_id: int, code: str, validated: bool = Depends(validate_totp_code)):
    credentials = fetch_secret_key(member_id)
    is_valid = validate_totp_code(code, credentials)
    
    if is_valid:
        return PlainTextResponse("true")
    else:
        return PlainTextResponse("false")
    
@app.get('/account/spent/{player_name}', response_model=int)
def get_player_spent(player_name: str):
    try:
        total_paid = fetch_and_calculate_paid(player_name)
        if total_paid == -1:
            raise HTTPException(status_code=500, detail="Error fetching data from the database")

        return total_paid
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/account/donate/{username}")
def read_donation_data(username: str):
    donation_data = retrieve_donation_data_for_user(username)
    return donation_data

@app.get("/account/vote/{username}")
def read_vote_data(username: str):
    # Call the count_unclaimed_users function with the specified username
    count = count_unclaimed_votes(username)

    if count is not None:
        return count
    else:
        return 0