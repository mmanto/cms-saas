"""Credenciales de integraciones por club (AFIP/ARCA, MercadoPago, WhatsApp).

Se guardan cifradas en ``tenant_credentials``. RLS garantiza que un club nunca
puede leer ni escribir las de otro, incluso con un bug de filtrado en la query.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import TenantContext, current_tenant_user
from app.crypto import decrypt_payload, encrypt_payload, mask
from app.models import TenantCredential

router = APIRouter(
    prefix="/credentials",
    tags=["credentials"],
    dependencies=[Depends(current_tenant_user)],
)

PROVIDERS = ("afip", "mercadopago", "whatsapp")

# Campos que nunca se devuelven en claro.
SECRET_FIELDS = {
    "password",
    "token",
    "access_token",
    "secret",
    "private_key",
    "client_secret",
    "api_key",
    "certificate_password",
}


class CredentialIn(BaseModel):
    payload: dict[str, str] = Field(min_length=1)


def _validate_provider(provider: str) -> str:
    provider = provider.strip().lower()
    if provider not in PROVIDERS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"provider desconocido, usar uno de {', '.join(PROVIDERS)}",
        )
    return provider


@router.get("")
async def list_credentials(ctx: TenantContext = Depends(current_tenant_user)) -> list[dict]:
    rows = (
        await ctx.session.scalars(
            select(TenantCredential).order_by(TenantCredential.provider)
        )
    ).all()
    result = []
    for row in rows:
        fields = sorted(decrypt_payload(row.ciphertext))
        result.append(
            {
                "provider": row.provider,
                "fields": fields,
                "updated_at": row.updated_at.isoformat(),
            }
        )
    return result


@router.put("/{provider}")
async def upsert_credential(
    provider: str,
    body: CredentialIn,
    ctx: TenantContext = Depends(current_tenant_user),
) -> dict:
    provider = _validate_provider(provider)
    ciphertext = encrypt_payload(body.payload)

    statement = (
        insert(TenantCredential)
        .values(tenant_id=ctx.tenant.id, provider=provider, ciphertext=ciphertext)
        .on_conflict_do_update(
            index_elements=[TenantCredential.tenant_id, TenantCredential.provider],
            set_={"ciphertext": ciphertext},
        )
    )
    await ctx.session.execute(statement)

    sample = next(iter(sorted(body.payload.values())), "")
    return {
        "provider": provider,
        "stored": True,
        "fields": sorted(body.payload),
        "preview": mask(sample),
    }


@router.delete("/{provider}")
async def delete_credential(
    provider: str,
    ctx: TenantContext = Depends(current_tenant_user),
) -> dict:
    provider = _validate_provider(provider)
    result = await ctx.session.execute(
        delete(TenantCredential).where(TenantCredential.provider == provider)
    )
    return {"provider": provider, "deleted": result.rowcount or 0}


@router.get("/{provider}/fields")
async def reveal_fields(
    provider: str,
    ctx: TenantContext = Depends(current_tenant_user),
) -> dict:
    """Devuelve los campos NO secretos. Los secretos se enmascaran siempre."""
    provider = _validate_provider(provider)
    row = await ctx.session.scalar(
        select(TenantCredential).where(TenantCredential.provider == provider)
    )
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="provider sin configurar")
    payload = decrypt_payload(row.ciphertext)
    return {
        "provider": provider,
        "fields": {
            key: ("********" if key.lower() in SECRET_FIELDS else value)
            for key, value in sorted(payload.items())
        },
    }
