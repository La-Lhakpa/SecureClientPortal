"""
Centralized security utilities for authentication and password management.
All password hashing and verification should use functions from this module.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from ..config import get_settings


# Single, consistent CryptContext instance for all password operations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string (bcrypt format)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password using bcrypt.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored bcrypt hash
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        result = pwd_context.verify(plain_password, hashed_password)
        # Log hash scheme for debugging (safe - no password exposure)
        if hashed_password:
            scheme = hashed_password.split("$")[0] if "$" in hashed_password else "unknown"
            print(f"[SECURITY] Password verification - Scheme: {scheme}, Result: {result}")
        return result
    except Exception as e:
        print(f"[SECURITY] Password verification error: {e}")
        return False


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in token
        expires_minutes: Token expiration time in minutes (uses default from settings if None)
        
    Returns:
        Encoded JWT token string
    """
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.jwt_expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict if valid, None otherwise
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def normalize_email(email: str) -> str:
    """
    Normalize email address: trim whitespace and convert to lowercase.
    
    Args:
        email: Email address string
        
    Returns:
        Normalized email address
    """
    return email.strip().lower()


def hash_access_code(access_code: str) -> str:
    """
    Hash a transfer access code using the same bcrypt context.
    """
    return pwd_context.hash(access_code)


def verify_access_code(access_code: str, access_code_hash: str) -> bool:
    """
    Verify a transfer access code against its stored hash.
    """
    try:
        return pwd_context.verify(access_code, access_code_hash)
    except Exception as e:
        print(f"[SECURITY] Access code verification error: {e}")
        return False


def create_transfer_access_token(transfer_id: int, receiver_id: int, expires_minutes: int = 15) -> str:
    """
    Create a short-lived token that grants access to a specific transfer for a receiver.
    """
    settings = get_settings()
    to_encode = {
        "typ": "transfer",
        "tid": str(transfer_id),
        "rid": str(receiver_id),
    }
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_transfer_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a transfer access token.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("typ") != "transfer":
            return None
        return payload
    except JWTError:
        return None
