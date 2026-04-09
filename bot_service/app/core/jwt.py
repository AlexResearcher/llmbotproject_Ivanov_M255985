from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import settings


class TokenValidationError(ValueError):
    """Raised when JWT is malformed or invalid."""


class TokenExpiredValidationError(TokenValidationError):
    """Raised when JWT is expired."""


def decode_and_validate(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_alg],
        )
    except ExpiredSignatureError as exc:
        raise TokenExpiredValidationError("Token has expired.") from exc
    except JWTError as exc:
        raise TokenValidationError("Invalid token.") from exc

    if not payload.get("sub"):
        raise TokenValidationError("Token payload is missing 'sub'.")

    return payload
