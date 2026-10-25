"""Login y perfil del usuario del club."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.api.deps import TenantContext, current_tenant_user, tenant_context
from app.models import TenantUser
from app.security import create_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class TenantOut(BaseModel):
    id: str
    slug: str
    name: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant: TenantOut


def _tenant_out(ctx: TenantContext) -> TenantOut:
    return TenantOut(id=str(ctx.tenant.id), slug=ctx.tenant.slug, name=ctx.tenant.name)


@router.post("/login", response_model=TokenOut)
async def login(
    payload: LoginRequest,
    ctx: TenantContext = Depends(tenant_context),
) -> TokenOut:
    """El club sale del Host: el mismo email en otro club no es la misma cuenta."""
    email = payload.email.strip().lower()
    user = await ctx.session.scalar(
        select(TenantUser).where(TenantUser.email == email)
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="credenciales invalidas")

    token = create_token(
        subject=str(user.id), scope="tenant", tenant_id=str(ctx.tenant.id)
    )
    return TokenOut(access_token=token, tenant=_tenant_out(ctx))


@router.get("/me")
async def me(ctx: TenantContext = Depends(current_tenant_user)) -> dict:
    assert ctx.user is not None
    return {
        "id": str(ctx.user.id),
        "email": ctx.user.email,
        "role": ctx.user.role,
        "tenant": _tenant_out(ctx).model_dump(),
        "host": ctx.host,
    }
