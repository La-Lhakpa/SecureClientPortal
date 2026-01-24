from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from email_validator import validate_email, EmailNotValidError
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from .. import schemas, models
from ..database import get_db
from ..core.security import verify_password, hash_password, create_access_token, normalize_email
from ..logger import setup_audit_logger
from ..config import get_settings


router = APIRouter(prefix="/auth", tags=["auth"])
audit_log = setup_audit_logger()


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Normalize email (trim + lowercase)
    normalized_email = normalize_email(user_in.email)
    print(f"[REGISTER] Attempting to register user with email: {normalized_email}")
    
    # Strict email validation with deliverability check
    print(f"[REGISTER] Validating email format and deliverability...")
    try:
        # Validate email format and check MX record for deliverability
        email_info = validate_email(
            normalized_email,
            check_deliverability=True  # Check MX record
        )
        # Use the normalized email from validator
        validated_email = email_info.normalized
        print(f"[REGISTER] Email validated successfully. Normalized: {validated_email}")
    except EmailNotValidError as e:
        print(f"[REGISTER] Email validation failed: {str(e)}")
        error_msg = str(e)
        if "domain" in error_msg.lower() or "mx" in error_msg.lower() or "deliverable" in error_msg.lower():
            error_msg = "Email domain is not deliverable"
        else:
            error_msg = "Invalid email format"
        audit_log.info("register_failed email=%s reason=email_validation_failed", normalized_email)
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error_msg)
    
    # Check if email already exists (using normalized email)
    print(f"[REGISTER] Checking if email exists in database...")
    existing_email = db.query(models.User).filter(models.User.email == validated_email).first()
    if existing_email:
        print(f"[REGISTER] Email already exists: {validated_email}")
        audit_log.info("register_failed email=%s reason=email_exists", validated_email)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    print(f"[REGISTER] Email is available. Hashing password...")
    # Hash password using centralized function
    password_hash = hash_password(user_in.password)
    print(f"[REGISTER] Password hashed. Hash length: {len(password_hash)}")
    print(f"[REGISTER] Hash scheme: {password_hash.split('$')[0] if '$' in password_hash else 'unknown'}")
    
    # Create user with normalized email
    print(f"[REGISTER] Creating User model instance...")
    user = models.User(
        email=validated_email,
        password_hash=password_hash,
    )
    
    print(f"[REGISTER] Adding user to session...")
    db.add(user)
    
    # Flush to get the ID before commit
    print(f"[REGISTER] Flushing session to get user ID...")
    try:
        db.flush()
        print(f"[REGISTER] Flush successful. User ID assigned: {user.id}")
    except Exception as e:
        print(f"[REGISTER] ERROR: Flush failed: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")
    
    print(f"[REGISTER] Committing transaction...")
    try:
        db.commit()
        print(f"[REGISTER] Transaction committed successfully")
    except Exception as e:
        print(f"[REGISTER] ERROR: Commit failed: {e}")
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create user: {str(e)}")
    
    print(f"[REGISTER] Refreshing user from database...")
    db.refresh(user)
    print(f"[REGISTER] User refreshed. ID: {user.id}, Email: {user.email}")
    
    # Verify user was actually saved by querying it back in a NEW session
    from ..database import SessionLocal
    verify_db = SessionLocal()
    try:
        verify_user = verify_db.query(models.User).filter(models.User.id == user.id).first()
        if verify_user:
            print(f"[REGISTER] VERIFIED: User exists in database with ID {verify_user.id}, Email: {verify_user.email}")
        else:
            print(f"[REGISTER] WARNING: User not found after commit! This indicates a transaction issue.")
    finally:
        verify_db.close()
    
    audit_log.info("register_success user_id=%s email=%s", user.id, user.email)
    print(f"[REGISTER] SUCCESS: User registered - ID: {user.id}, Email: {user.email}")
    return user


@router.post("/login", response_model=schemas.Token)
def login(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    # Normalize email (trim + lowercase) - must match registration normalization
    normalized_email = normalize_email(user_in.email)
    print(f"[LOGIN] Attempting login for email: {normalized_email}")
    
    # Find user by normalized email
    print(f"[LOGIN] Querying database for user with normalized email: {normalized_email}")
    user = db.query(models.User).filter(models.User.email == normalized_email).first()
    
    if not user:
        print(f"[LOGIN] User not found in database for email: {normalized_email}")
        # Check total user count for debugging
        total_users = db.query(models.User).count()
        print(f"[LOGIN] Total users in database: {total_users}")
        # Use generic error message to avoid user enumeration
        audit_log.info("login_failed email=%s reason=user_not_found", normalized_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    print(f"[LOGIN] User found - ID: {user.id}, Email: {user.email}")
    
    # Check if user is a Google OAuth user (no password_hash)
    if not user.password_hash:
        print(f"[LOGIN] User is a Google OAuth user (no password_hash). Password login not available.")
        audit_log.info("login_failed email=%s reason=google_oauth_user", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses Google Sign-In. Please use Google to log in."
        )
    
    print(f"[LOGIN] Stored password hash length: {len(user.password_hash)}")
    hash_scheme = user.password_hash.split("$")[0] if "$" in user.password_hash else "unknown"
    print(f"[LOGIN] Stored hash scheme: {hash_scheme}")
    print(f"[LOGIN] Verifying password using bcrypt...")
    
    # Verify password using centralized function
    password_valid = verify_password(user_in.password, user.password_hash)
    print(f"[LOGIN] Password verification result: {password_valid}")
    
    if not password_valid:
        print(f"[LOGIN] Password verification FAILED - password does not match stored hash")
        audit_log.info("login_failed email=%s reason=password_mismatch", normalized_email)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    print(f"[LOGIN] Password verified successfully. Creating JWT token...")
    token = create_access_token({"sub": str(user.id)})
    print(f"[LOGIN] Token created. Length: {len(token)}")
    
    audit_log.info("login_success user_id=%s email=%s", user.id, user.email)
    print(f"[LOGIN] SUCCESS: Login successful - User ID: {user.id}, Email: {user.email}")
    
    return schemas.Token(
        access_token=token,
        token_type="bearer",
        user=schemas.UserOut(
            id=user.id,
            email=user.email,
            created_at=user.created_at
        )
    )


@router.post("/google", response_model=schemas.Token)
def google_login(google_token: schemas.GoogleToken, db: Session = Depends(get_db)):
    """
    Authenticate user with Google ID token.
    Verifies the token with Google, extracts email, and creates/updates user.
    Returns our app's JWT token.
    """
    settings = get_settings()
    
    if not settings.google_client_id:
        print("[GOOGLE_LOGIN] ERROR: GOOGLE_CLIENT_ID not configured")
        audit_log.warning("google_login_failed reason=not_configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google login not configured. Please contact support."
        )
    
    id_token_str = google_token.id_token
    print(f"[GOOGLE_LOGIN] Attempting to verify Google ID token...")
    print(f"[GOOGLE_LOGIN] Token length: {len(id_token_str) if id_token_str else 0}")
    print(f"[GOOGLE_LOGIN] Using Client ID: {settings.google_client_id}")
    
    try:
        # Verify the Google ID token with clock skew tolerance
        # Allow up to 60 seconds of clock skew to handle time differences
        # This is recommended by Google for handling clock synchronization issues
        payload = id_token.verify_oauth2_token(
            id_token_str,
            grequests.Request(),
            settings.google_client_id,
            clock_skew_in_seconds=60  # Allow 60 seconds of clock skew (recommended by Google)
        )
        print(f"[GOOGLE_LOGIN] Token verified successfully")
        
        # Extract email and verification status
        email = payload.get("email")
        email_verified = payload.get("email_verified", False)
        google_sub = payload.get("sub")
        
        print(f"[GOOGLE_LOGIN] Email: {email}, Verified: {email_verified}, Sub: {google_sub}")
        
        # Reject if no email
        if not email:
            print(f"[GOOGLE_LOGIN] ERROR: No email in Google token payload")
            audit_log.warning("google_login_failed reason=no_email")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account email not found"
            )
        
        # Reject if email not verified
        if not email_verified:
            print(f"[GOOGLE_LOGIN] ERROR: Email not verified by Google")
            audit_log.warning("google_login_failed email=%s reason=email_not_verified", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google email not verified"
            )
        
        # Normalize email
        normalized_email = normalize_email(email)
        print(f"[GOOGLE_LOGIN] Normalized email: {normalized_email}")
        
        # Find or create user
        user = db.query(models.User).filter(models.User.email == normalized_email).first()
        
        if not user:
            # Create new user (password_hash will be NULL for Google users)
            print(f"[GOOGLE_LOGIN] User not found, creating new user...")
            user = models.User(
                email=normalized_email,
                password_hash=None,  # NULL for Google OAuth users
            )
            db.add(user)
            db.flush()
            db.commit()
            db.refresh(user)
            print(f"[GOOGLE_LOGIN] New user created - ID: {user.id}, Email: {user.email}")
            audit_log.info("google_login_success user_id=%s email=%s action=created", user.id, user.email)
        else:
            # Existing user - update password_hash to NULL if it was set (allows switching to Google auth)
            if user.password_hash is not None:
                print(f"[GOOGLE_LOGIN] Existing user found, updating password_hash to NULL...")
                user.password_hash = None
                db.commit()
                db.refresh(user)
            print(f"[GOOGLE_LOGIN] Existing user found - ID: {user.id}, Email: {user.email}")
            audit_log.info("google_login_success user_id=%s email=%s action=logged_in", user.id, user.email)
        
        # Create our app's JWT token
        token = create_access_token({"sub": str(user.id)})
        print(f"[GOOGLE_LOGIN] JWT token created. Length: {len(token)}")
        
        return schemas.Token(
            access_token=token,
            token_type="bearer",
            user=schemas.UserOut(
                id=user.id,
                email=user.email,
                created_at=user.created_at
            )
        )
        
    except ValueError as e:
        # Invalid token - this is raised by google-auth when token verification fails
        error_msg = str(e)
        print(f"[GOOGLE_LOGIN] ERROR: Token verification failed - {error_msg}")
        print(f"[GOOGLE_LOGIN] Error type: ValueError")
        audit_log.warning("google_login_failed reason=token_verification_failed error=%s", error_msg)
        
        # Provide more helpful error message
        if "Token used too early" in error_msg or "too early" in error_msg.lower():
            detail_msg = "System clock is out of sync. Please sync your computer's clock with internet time and try again."
        elif "Token has wrong issuer" in error_msg or "Wrong number of segments" in error_msg:
            detail_msg = "Invalid Google token format. Please ensure the origin is authorized in Google Cloud Console."
        elif "Token has wrong audience" in error_msg or "audience" in error_msg.lower():
            detail_msg = "Token client ID mismatch. Please check GOOGLE_CLIENT_ID configuration."
        else:
            detail_msg = f"Invalid Google token: {error_msg}"
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail_msg
        )
    except Exception as e:
        # Catch any other exceptions (network errors, etc.)
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[GOOGLE_LOGIN] ERROR: Unexpected error ({error_type}) - {error_msg}")
        audit_log.error("google_login_failed reason=unexpected_error type=%s error=%s", error_type, error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {error_msg}"
        )
