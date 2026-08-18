import secrets
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_api_key() -> str:
    return secrets.token_urlsafe(32)

def hash_api_key(key: str) -> str:
    return pwd_context.hash(key)

def verify_api_key(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)