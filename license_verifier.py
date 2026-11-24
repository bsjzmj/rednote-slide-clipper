# encoding: utf-8
"""
Offline Ed25519 public-key license verification (<0.2ms, zero network calls).
Only the 32-byte Ed25519 public key is embedded here; the signing private key is offline.
"""

import base64
import json
import time
from datetime import datetime
from pathlib import Path
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

PUBLIC_KEY_HEX = "09d50442d1e8de987a5bac12f992d36f29c00edc3255d5d0dbff4b4ce47993ed"
LICENSE_FILE = Path.home() / ".rednote_slide_clipper_license.json"


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * ((4 - len(segment) % 4) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def verify_license_token(token: str) -> dict:
    if not token or not isinstance(token, str):
        return {"valid": False, "reason": "Empty token"}
    parts = token.strip().split(".")
    if len(parts) != 3 or parts[0] != "RMC1":
        return {"valid": False, "reason": "Invalid token format"}
    try:
        payload_bytes = _b64url_decode(parts[1])
        sig_bytes = _b64url_decode(parts[2])
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(PUBLIC_KEY_HEX))
        pub_key.verify(sig_bytes, payload_bytes)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (InvalidSignature, ValueError, json.JSONDecodeError):
        return {"valid": False, "reason": "Signature verification failed"}

    exp = int(payload.get("exp", 0) or 0)
    if exp > 0 and int(time.time()) > exp:
        return {"valid": False, "reason": "License expired"}

    exp_str = "Lifetime" if exp == 0 else datetime.fromtimestamp(exp).strftime("%Y-%m-%d")
    return {
        "valid": True,
        "tier": "Pro",
        "user": payload.get("u", "pro_user"),
        "expires": exp_str,
    }


def activate_token(token: str) -> dict:
    res = verify_license_token(token)
    if not res["valid"]:
        return res
    LICENSE_FILE.write_text(
        json.dumps({"token": token.strip()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return res


def get_license_status() -> dict:
    if not LICENSE_FILE.exists():
        return {"is_pro": False, "tier": "Free", "expires": "-"}
    try:
        saved = json.loads(LICENSE_FILE.read_text(encoding="utf-8"))
        res = verify_license_token(saved.get("token", ""))
        if res["valid"]:
            return {
                "is_pro": True,
                "tier": "Pro",
                "user": res["user"],
                "expires": res["expires"],
            }
    except Exception:
        pass
    return {"is_pro": False, "tier": "Free", "expires": "-"}
