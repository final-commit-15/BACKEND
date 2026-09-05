from passlib.context import CryptContext
from ..config.settings import settings

# Support both Argon2 and bcrypt for backward compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,
    argon2__time_cost=3,
    argon2__parallelism=4,
    argon2__hash_len=32,
    argon2__salt_size=16,
    bcrypt__rounds=12,
)

def hash_password(password: str) -> str:
    """Hash a password using Argon2 (preferred) or bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain, hashed)

def needs_rehash(hashed: str) -> bool:
    """Check if a hash needs to be updated to the current algorithm."""
    return pwd_context.needs_update(hashed)