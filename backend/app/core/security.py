import base64
import binascii
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

password_hash = PasswordHash.recommended()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set; add it to backend/.env")

ACCESS_TOKEN_MINUTES = 60


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user_id: str) -> str:
    expires_at = int((datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)).timestamp())
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64url_encode(json.dumps({"sub": user_id, "exp": expires_at}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}"
    signature = hmac.new(JWT_SECRET_KEY.encode(), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".")
        header = json.loads(_b64url_decode(header_part))
        payload = json.loads(_b64url_decode(payload_part))
        if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("Unsupported token header")
        signing_input = f"{header_part}.{payload_part}"
        expected = hmac.new(JWT_SECRET_KEY.encode(), signing_input.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(signature_part)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Invalid token signature")
        if not isinstance(payload, dict) or not isinstance(payload.get("sub"), str):
            raise ValueError("Invalid token subject")
        expiry = payload.get("exp")
        if type(expiry) is not int or expiry <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("Expired or invalid token")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError, binascii.Error) as exc:
        raise ValueError("Invalid access token") from exc