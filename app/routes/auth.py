"""Authentication routes for login and user management."""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.models import User, get_db
from app.schemas import UserCreate, UserResponse, TokenResponse, UserUpdate
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from typing import List

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint - authenticate user and return JWT token.
    
    Args:
        form_data: Username and password
        db: Database session
        
    Returns:
        Token response with access token and user info
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    token = create_access_token(user.id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.from_orm(user)
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register new user (currently open - should restrict in production).
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        Created user
    """
    # Check if user already exists
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        roles=user_data.roles
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user info.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User information
    """
    return UserResponse.from_orm(current_user)


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all users (admin only).
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        List of users
    """
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    users = db.query(User).all()
    return [UserResponse.from_orm(u) for u in users]


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user (self or admin).
    
    Args:
        user_id: User ID
        user_update: Update data
        db: Database session
        current_user: Current user
        
    Returns:
        Updated user
    """
    # Check permission
    if user_id != current_user.id and "admin" not in current_user.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if user_update.email:
        user.email = user_update.email
    
    if user_update.roles and "admin" in current_user.roles:
        user.roles = user_update.roles
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)
