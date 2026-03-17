from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth
from jose import jwt
from datetime import datetime, timedelta

from app.config import get_settings
from app.database import async_session
from app.services.user_service import UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])

settings = get_settings()

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'prompt': 'select_account'  # Force account selection screen
    }
)


def create_token(user_id: int, google_id: str, email: str, name: str, avatar_url: str | None) -> str:
    """Create a JWT token for the user."""
    expires = datetime.utcnow() + timedelta(days=7)
    token = jwt.encode(
        {
            "user_id": user_id,
            "google_id": google_id,
            "email": email,
            "name": name,
            "avatar_url": avatar_url,
            "exp": expires
        },
        settings.secret_key,
        algorithm="HS256"
    )
    return token


@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth login."""
    client_id = settings.google_client_id
    client_secret = settings.google_client_secret
    
    print(f"DEBUG: GOOGLE_CLIENT_ID = '{client_id}'")
    print(f"DEBUG: GOOGLE_CLIENT_SECRET set = {bool(client_secret)}")
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail=f"Google OAuth not configured. GOOGLE_CLIENT_ID='{client_id}', GOOGLE_CLIENT_SECRET set={bool(client_secret)}"
        )
    
    # Store redirect URL in session for after auth
    redirect_to = request.query_params.get("redirect", "/")
    request.session["redirect_after_auth"] = redirect_to
    
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, response: Response):
    """Handle Google OAuth callback."""
    print(f"DEBUG: Callback received. Query params: {dict(request.query_params)}")
    
    try:
        token = await oauth.google.authorize_access_token(request)
        print(f"DEBUG: Got token: {token}")
    except Exception as e:
        print(f"DEBUG: OAuth error: {e}")
        raise HTTPException(status_code=400, detail=f"OAuth authentication failed: {str(e)}")
    
    # Get user info from token
    user_info = token.get('userinfo')
    print(f"DEBUG: User info: {user_info}")
    
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to get user info from Google")
    
    google_id = user_info.get('sub')
    email = user_info.get('email')
    name = user_info.get('name', email.split('@')[0])  # Fallback to email username if no name
    avatar_url = user_info.get('picture')
    
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Invalid user info from Google")
    
    # Find or create user in database
    async with async_session() as db:
        user_service = UserService(db)
        user = await user_service.get_user_by_google_id(google_id)
        
        if user:
            # Update user info if changed
            if user.name != name or user.avatar_url != avatar_url:
                user = await user_service.update_user(user, name=name, avatar_url=avatar_url)
        else:
            # Check if email already exists
            existing_user = await user_service.get_user_by_email(email)
            if existing_user:
                # Link Google account to existing email
                user = await user_service.update_user(existing_user)
                user.google_id = google_id
                await db.commit()
            else:
                # Create new user
                user = await user_service.create_user(
                    google_id=google_id,
                    email=email,
                    name=name,
                    avatar_url=avatar_url
                )
    
    # Create JWT token
    auth_token = create_token(user.id, user.google_id, user.email, user.name, user.avatar_url)
    print(f"DEBUG: Created token for user: {user.name}")
    
    # Build redirect URL
    redirect_to = request.session.get("redirect_after_auth", "/home")
    frontend_url = f"{settings.frontend_url}{redirect_to}"
    
    # Create response with redirect and cookie
    
    # Set cookie on a response first, then redirect
    response = RedirectResponse(url=frontend_url, status_code=302)
    response.set_cookie(
        key="auth_token",
        value=auth_token,
        httponly=True,
        max_age=3600 * 24 * 7,  # 7 days
        samesite="lax",
        secure=settings.environment == "production"
    )
    print(f"DEBUG: Cookie set, redirecting to: {frontend_url}")
    
    return response


@router.post("/logout")
async def logout(response: Response):
    """Logout the user."""
    response.delete_cookie("auth_token")
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(request: Request):
    """Get current authenticated user info."""
    token = request.cookies.get("auth_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # If avatar_url is missing from token (old token), fetch from database
        avatar_url = payload.get("avatar_url")
        if not avatar_url:
            async with async_session() as db:
                user_service = UserService(db)
                user = await user_service.get_user_by_google_id(payload["google_id"])
                if user:
                    avatar_url = user.avatar_url
        
        return {
            "user_id": payload["user_id"],
            "google_id": payload["google_id"],
            "email": payload["email"],
            "name": payload["name"],
            "avatar_url": avatar_url
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None
