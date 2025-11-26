from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List
import jwt
from datetime import datetime, timedelta
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# configuración
login_user = "admin"
login_password = "1234"

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION_MINUTES"))

# Configuraciion de la app y usar tokens en el swaggger (el usePkc)
app = FastAPI(
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

client = MongoClient(MONGODB_URL)
db = client["prueba_backend"]
numbers_collection = db["numbers"]

security = HTTPBearer()

# Requests
class LoginRequest(BaseModel):
    username: str
    password: str

class NumberRequest(BaseModel):
    number: int

# Responses
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    
class NumberResponse(BaseModel):
    id: str
    number: int
    created_at: str
    
# Servicios
def create_token(username: str) -> dict:
    expiration = datetime.now() + timedelta(minutes = JWT_EXPIRATION)
    payload = {
        "sub": username,
        "exp": expiration
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer"}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        
        if username is None:
            raise HTTPException(
                status_code = status.HTTP_401_UNAUTHORIZED,
                detail = "Token invalido"
            )
            
        return username
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token expirado"
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Token invalido"
        )
        
async def login_service(credentials: LoginRequest):
    if credentials.username != login_user or credentials.password != login_password:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Credenciales incorrectas"
        )
    return create_token(credentials.username)

async def create_numbers_service(number_data: NumberRequest):
    number_model = {
        "number": number_data.number,
        "created_at": datetime.now().isoformat()
    }
    
    result = numbers_collection.insert_one(number_model)
    return NumberResponse(
        id = str(result.inserted_id),
        number = number_model["number"],
        created_at = number_model["created_at"]
    )

async def get_numbers_service():
    cursor = numbers_collection.find({})
    numbers_list = []
    for doc in cursor:
        numbers_list.append(
            NumberResponse(
                id = str(doc["_id"]),
                number = doc["number"],
                created_at = doc["created_at"]
            )
        )
    return numbers_list

# Endpoints
@app.get("/", tags = ["Home"])
async def home():
    return {"/docs para ver la documentación con Swagger",
            "/login para obtener token de autenticación",
            "/numbers (Get) para crear un número (requiere token)",
            "/numbers (Post) para obtener todos los números (requiere token)"},
        

@app.post("/login", response_model = LoginResponse, tags = ["Login"])
async def login(credentials: LoginRequest):
    return await login_service(credentials)

@app.post("/numbers", response_model = NumberResponse, status_code = status.HTTP_201_CREATED, tags = ["Números"])
async def create_number(
    number_data: NumberRequest,
    username: str = Depends(verify_token)):
    return await create_numbers_service(number_data)
    

@app.get("/numbers", response_model=List[NumberResponse], tags = ["Numbers"])
async def get_numbers(username: str = Depends(verify_token)):
    return await get_numbers_service()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)