import os
import secrets
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User

logger = logging.getLogger(__name__)

security = HTTPBearer()

def get_automation_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates the N8N_AUTOMATION_API_KEY from the Authorization Bearer header.
    Returns the automation 'system' user, creating it if it doesn't exist.
    """
    expected_api_key = os.getenv("N8N_AUTOMATION_API_KEY")
    
    if not expected_api_key:
        logger.error("N8N_AUTOMATION_API_KEY is not set in environment.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Automation API key is not configured on the server."
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(credentials.credentials, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find or create an automation user to own the generated projects
    automation_email = "n8n_automation@system.local"
    user = db.query(User).filter(User.email == automation_email).first()
    
    if not user:
        try:
            from auth.security import get_password_hash
            # Create a dummy user with a random password
            user = User(
                email=automation_email,
                password_hash=get_password_hash(secrets.token_urlsafe(32)),
                role="admin",
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("Created system automation user.")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create automation user: {e}")
            # Fallback: just return the first user in the DB if possible
            first_user = db.query(User).first()
            if first_user:
                return first_user
            raise HTTPException(status_code=500, detail="Failed to initialize automation user")

    return user
