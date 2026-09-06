from fastapi import APIRouter
from app.core.deps import CurrentUser, DBSession
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, UserOut
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(req: RegisterRequest, db: DBSession):
    user = await UserService.register(req, db)
    return UserOut.from_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: DBSession):
    return await UserService.login(req, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: DBSession):
    return await UserService.refresh_tokens(req.refresh_token, db)


@router.get("/me", response_model=UserOut)
async def me(current_user: CurrentUser):
    return UserOut.from_user(current_user)
