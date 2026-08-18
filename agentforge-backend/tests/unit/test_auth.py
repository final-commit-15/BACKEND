import pytest
from src.agentforge_backend.security.password import hash_password, verify_password

def test_password_hashing():
    plain = "secret"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)