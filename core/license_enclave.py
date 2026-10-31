# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Proprietary License & Evaluation Enclave (Ed25519)

- Production use requires an Ed25519-signed license issued by ThinkConnect IA
  (Carlos Ferro - carlos@thinkconnect.com.ar). Only the PUBLIC verification key
  lives in this file; the signing key never leaves ThinkConnect infrastructure.
- Without a license, a 5-day (120 h) evaluation window applies, with volume and
  transaction caps.

Evaluation-state hardening (v2):
- The expiration is DERIVED from the first-launch time; it is never read from disk.
- The full state record is sealed with an HMAC bound to this machine's fingerprint.
- The state is mirrored in several independent locations; deleting one copy does
  not reset the trial, and the most restrictive surviving copy always wins.
- A tampered or corrupted copy locks the enclave (fail-closed) instead of
  silently starting a fresh trial.
- A monotonic "last seen" timestamp detects system-clock rollbacks at any moment.
"""

import os
import sys
import json
import time
import uuid
import hmac
import base64
import hashlib
import platform
import tempfile
from typing import Dict, Any, Optional, List

from cryptography.hazmat.primitives.asymmetric import ed25519

# ThinkConnect IA - Master Public Verification Key (Ed25519).
# The matching private key is held exclusively by ThinkConnect and is never published.
THINKCONNECT_MASTER_PUBLIC_KEY_HEX = "a27ef55bd1f323f1dc6e420ab17dbc831d5f633c0717467a2377fbd7959c7e80"

EVALUATION_WINDOW_SECONDS = 5 * 24 * 3600  # Exactly 5 days (120 hours)
MAX_TRIAL_TRANSACTIONS = 100
MAX_TRIAL_VOLUME_USD = 2500.0
CLOCK_ROLLBACK_TOLERANCE_SECONDS = 300
STATE_SCHEMA_VERSION = 2
STATE_FILENAME = ".agenticpay_enclave.state"
CONTACT = "carlos@thinkconnect.com.ar"


def _machine_fingerprint() -> str:
    """Stable, non-reversible identifier of the host running the bridge."""
    parts = [platform.node(), sys.platform, platform.machine(), format(uuid.getnode(), "x")]
    for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                parts.append(f.read().strip())
                break
        except Exception:
            continue
    if sys.platform == "win32":
        try:
            import winreg  # noqa: WPS433
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography") as k:
                parts.append(winreg.QueryValueEx(k, "MachineGuid")[0])
        except Exception:
            pass
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _default_state_locations() -> List[str]:
    """Independent mirror locations for the evaluation state."""
    locations = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), STATE_FILENAME),
        os.path.join(os.path.expanduser("~"), ".agenticpay", STATE_FILENAME),
        os.path.join(tempfile.gettempdir(), ".agenticpay_cache", STATE_FILENAME),
    ]
    if sys.platform == "win32":
        base = os.environ.get("PROGRAMDATA") or os.environ.get("LOCALAPPDATA")
        if base:
            locations.append(os.path.join(base, "AgenticPay", STATE_FILENAME))
    else:
        locations.append(os.path.join("/var/tmp", ".agenticpay", STATE_FILENAME))
    return locations


class LicenseEnclave:
    def __init__(self, state_dir: Optional[str] = None):
        """
        state_dir: when provided (tests / sandboxes), all mirror copies are kept
        inside that directory instead of the system-wide default locations.
        """
        if state_dir:
            self.state_locations = [
                os.path.join(state_dir, "mirror_a", STATE_FILENAME),
                os.path.join(state_dir, "mirror_b", STATE_FILENAME),
                os.path.join(state_dir, "mirror_c", STATE_FILENAME),
            ]
        else:
            self.state_locations = _default_state_locations()

        self._pubkey = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(THINKCONNECT_MASTER_PUBLIC_KEY_HEX)
        )
        self._fingerprint = _machine_fingerprint()
        self._seal_key = hashlib.sha256(
            f"{self._fingerprint}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}:agenticpay-state-v2".encode("utf-8")
        ).digest()
        self.tamper_reason: Optional[str] = None
        self.state = self._load_state()

    # ------------------------------------------------------------------ #
    # State sealing & persistence
    # ------------------------------------------------------------------ #
    def _seal(self, record: Dict[str, Any]) -> str:
        body = {k: v for k, v in record.items() if k != "seal"}
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(self._seal_key, canonical, hashlib.sha256).hexdigest()

    def _new_state(self) -> Dict[str, Any]:
        now = time.time()
        state = {
            "schema": STATE_SCHEMA_VERSION,
            "fingerprint": self._fingerprint,
            "first_launch_epoch": round(now, 3),
            "last_seen_epoch": round(now, 3),
            "tx_count": 0,
            "volume_usd": 0.0,
            "locked_reason": None,
        }
        state["seal"] = self._seal(state)
        return state

    def _read_copy(self, path: str) -> Optional[Dict[str, Any]]:
        """Returns the record, None if absent, or raises ValueError if tampered."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            raise ValueError("STATE_CORRUPTED")
        if not isinstance(record, dict) or not hmac.compare_digest(str(record.get("seal", "")), self._seal(record)):
            raise ValueError("STATE_SEAL_MISMATCH")
        if record.get("fingerprint") != self._fingerprint:
            raise ValueError("STATE_MACHINE_MISMATCH")
        if record.get("schema") != STATE_SCHEMA_VERSION:
            raise ValueError("STATE_SCHEMA_MISMATCH")
        return record

    def _load_state(self) -> Dict[str, Any]:
        valid: List[Dict[str, Any]] = []
        for path in self.state_locations:
            try:
                record = self._read_copy(path)
                if record is not None:
                    valid.append(record)
            except ValueError as exc:
                if self.tamper_reason is None:
                    self.tamper_reason = str(exc)

        if valid:
            # Most restrictive view across all surviving mirrors wins.
            merged = {
                "schema": STATE_SCHEMA_VERSION,
                "fingerprint": self._fingerprint,
                "first_launch_epoch": min(r["first_launch_epoch"] for r in valid),
                "last_seen_epoch": max(r["last_seen_epoch"] for r in valid),
                "tx_count": max(r["tx_count"] for r in valid),
                "volume_usd": max(r["volume_usd"] for r in valid),
                "locked_reason": next((r["locked_reason"] for r in valid if r.get("locked_reason")), None),
            }
        else:
            merged = self._new_state()

        if self.tamper_reason and not merged.get("locked_reason"):
            merged["locked_reason"] = f"TAMPER_DETECTED_{self.tamper_reason}"

        merged["seal"] = self._seal(merged)
        self._persist(merged)
        return merged

    def _persist(self, record: Dict[str, Any]) -> None:
        record["seal"] = self._seal(record)
        payload = json.dumps(record, indent=2)
        for path in self.state_locations:
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(payload)
            except Exception:
                continue

    def _lock(self, reason: str) -> None:
        if not self.state.get("locked_reason"):
            self.state["locked_reason"] = reason
            self._persist(self.state)

    # ------------------------------------------------------------------ #
    # Authorization
    # ------------------------------------------------------------------ #
    @staticmethod
    def _deny(error: str, message: str) -> Dict[str, Any]:
        return {
            "authorized": False,
            "error": error,
            "message": message,
            "action_required": f"To unlock production use, contact Carlos Ferro at {CONTACT}",
        }

    def _verify_license_token(self, token: str, now: float) -> Dict[str, Any]:
        parts = token.split(".")
        if len(parts) != 4 or parts[0] != "THINKCONNECT-v1" or parts[1] != "ed25519":
            return self._deny("TAMPER_DETECTED_FORGED_LICENSE", "Malformed license key.")
        try:
            payload_bytes = base64.urlsafe_b64decode(parts[2] + "==")
            sig_bytes = base64.urlsafe_b64decode(parts[3] + "==")
            self._pubkey.verify(sig_bytes, payload_bytes)
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception:
            return self._deny(
                "TAMPER_DETECTED_FORGED_LICENSE",
                "Cryptographic signature mismatch. License key has been forged or corrupted.",
            )

        expires_at = payload.get("expires_at", 0)
        if expires_at and now > expires_at:
            return self._deny("LICENSE_EXPIRED", f"Enterprise license expired on {time.ctime(expires_at)}.")

        bound_fp = payload.get("machine_fingerprint")
        if bound_fp and bound_fp != self._fingerprint:
            return self._deny("LICENSE_MACHINE_MISMATCH", "This license is bound to a different host.")

        entropy = hashlib.sha256(
            f"ENTERPRISE:{payload.get('client')}:{payload.get('issued_at')}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}".encode()
        ).hexdigest()
        return {
            "authorized": True,
            "mode": payload.get("tier", "ENTERPRISE_PRODUCTION"),
            "client": payload.get("client"),
            "entropy": entropy,
        }

    def verify_execution_authorization(self, amount: float = 0.0) -> Dict[str, Any]:
        now = time.time()

        env_key = os.environ.get("AGENTICPAY_LICENSE_KEY", "").strip()
        if env_key:
            return self._verify_license_token(env_key, now)

        # --- Evaluation mode ---
        if self.state.get("locked_reason"):
            return self._deny(
                self.state["locked_reason"],
                "Evaluation enclave is permanently locked due to state tampering or clock manipulation.",
            )

        first_launch = self.state["first_launch_epoch"]
        expiration = first_launch + EVALUATION_WINDOW_SECONDS  # derived, never trusted from disk

        if now < self.state["last_seen_epoch"] - CLOCK_ROLLBACK_TOLERANCE_SECONDS or now < first_launch - CLOCK_ROLLBACK_TOLERANCE_SECONDS:
            self._lock("TAMPER_DETECTED_CLOCK_ROLLBACK")
            return self._deny("TAMPER_DETECTED_CLOCK_ROLLBACK", "System clock rollback detected. Enclave permanently locked.")

        self.state["last_seen_epoch"] = round(max(self.state["last_seen_epoch"], now), 3)
        self._persist(self.state)

        if now > expiration:
            return self._deny(
                "EVALUATION_EXPIRED_5_DAYS",
                f"5-day evaluation window (120 hours) has expired. Elapsed: {round((now - first_launch) / 86400, 1)} days.",
            )
        if self.state["volume_usd"] + amount > MAX_TRIAL_VOLUME_USD:
            return self._deny(
                "EVALUATION_VOLUME_LIMIT_EXCEEDED",
                f"Evaluation volume cap of ${MAX_TRIAL_VOLUME_USD:,.2f} USD exceeded.",
            )
        if self.state["tx_count"] >= MAX_TRIAL_TRANSACTIONS:
            return self._deny(
                "EVALUATION_TX_LIMIT_EXCEEDED",
                f"Evaluation limit of {MAX_TRIAL_TRANSACTIONS} transactions reached.",
            )

        entropy = hashlib.sha256(
            f"TRIAL:{first_launch}:{self.state['tx_count']}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}".encode()
        ).hexdigest()
        return {
            "authorized": True,
            "mode": "COMMUNITY_TRIAL_5_DAYS",
            "hours_remaining": round(max(0.0, expiration - now) / 3600.0, 1),
            "tx_remaining": MAX_TRIAL_TRANSACTIONS - self.state["tx_count"],
            "volume_remaining_usd": round(MAX_TRIAL_VOLUME_USD - self.state["volume_usd"], 2),
            "entropy": entropy,
        }

    def record_settlement(self, amount: float) -> None:
        if os.environ.get("AGENTICPAY_LICENSE_KEY", "").strip():
            return  # licensed hosts do not consume the evaluation meter
        self.state["tx_count"] += 1
        self.state["volume_usd"] = round(self.state["volume_usd"] + amount, 2)
        self.state["last_seen_epoch"] = round(max(self.state["last_seen_epoch"], time.time()), 3)
        self._persist(self.state)
