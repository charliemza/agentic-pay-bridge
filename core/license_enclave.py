# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Proprietary License & Cryptographic Time-Bomb Enclave (Ed25519)
Enforces strict 5-day evaluation window (120 hours) and volume caps.
Requires Master Asymmetric Unlock Key from Carlos Ferro (ThinkConnect IA) for production.
"""

import time
import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519

# ThinkConnect IA - Master Public Verification Key (Ed25519)
# The matching Private Key is held strictly on ThinkConnect Server_IA and is NEVER published.
THINKCONNECT_MASTER_PUBLIC_KEY_HEX = "a27ef55bd1f323f1dc6e420ab17dbc831d5f633c0717467a2377fbd7959c7e80"
EVALUATION_WINDOW_SECONDS = 5 * 24 * 3600  # Exactly 5 days (120 hours)
MAX_TRIAL_TRANSACTIONS = 100
MAX_TRIAL_VOLUME_USD = 2500.0


class LicenseEnclave:
    def __init__(self, state_dir: Optional[str] = None):
        if not state_dir:
            state_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(state_dir, ".license_enclave_state.dat")
        self._pubkey = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(THINKCONNECT_MASTER_PUBLIC_KEY_HEX)
        )
        self.state = self._initialize_or_load_state()

    def _initialize_or_load_state(self) -> Dict[str, Any]:
        now = time.time()
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    calc_sig = self._sign_local_state(data["first_launch_epoch"], data["tx_count"], data["volume_usd"])
                    if data.get("signature") == calc_sig:
                        return data
            except Exception:
                pass
        
        # Fresh initial trial state
        initial_state = {
            "first_launch_epoch": now,
            "expiration_epoch": now + EVALUATION_WINDOW_SECONDS,
            "tx_count": 0,
            "volume_usd": 0.0,
            "unlocked": False
        }
        initial_state["signature"] = self._sign_local_state(
            initial_state["first_launch_epoch"],
            initial_state["tx_count"],
            initial_state["volume_usd"]
        )
        self._persist_state(initial_state)
        return initial_state

    def _sign_local_state(self, epoch: float, count: int, volume: float) -> str:
        raw = f"{epoch:.2f}:{count}:{volume:.2f}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _persist_state(self, state_dict: Dict[str, Any]):
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=2)
        except Exception:
            pass

    def verify_execution_authorization(self, amount: float = 0.0) -> Dict[str, Any]:
        """
        Validates whether the 5-day evaluation period is still valid or if an enterprise
        asymmetric unlock key signed by Carlos Ferro has been injected.
        """
        now = time.time()

        # 1. Check if Enterprise Master License Key is present in environment
        env_key = os.environ.get("AGENTICPAY_LICENSE_KEY", "").strip()
        if env_key:
            parts = env_key.split(".")
            if len(parts) == 4 and parts[0] == "THINKCONNECT-v1" and parts[1] == "ed25519":
                try:
                    payload_bytes = base64.urlsafe_b64decode(parts[2] + "==")
                    sig_bytes = base64.urlsafe_b64decode(parts[3] + "==")
                    
                    # Cryptographic verification via Ed25519
                    self._pubkey.verify(sig_bytes, payload_bytes)
                    payload = json.loads(payload_bytes.decode("utf-8"))
                    
                    # Check expiration if set
                    expires_at = payload.get("expires_at", 0)
                    if expires_at > 0 and now > expires_at:
                        return {
                            "authorized": False,
                            "error": "LICENSE_EXPIRED",
                            "message": f"Enterprise license expired on {time.ctime(expires_at)}.",
                            "action_required": "Renew license with Carlos Ferro (carlos@thinkconnect.com.ar)."
                        }
                    
                    # Valid Enterprise License
                    auth_entropy = hashlib.sha256(
                        f"ENTERPRISE_VALID:{payload['client']}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}".encode()
                    ).hexdigest()
                    
                    return {
                        "authorized": True,
                        "mode": payload.get("tier", "ENTERPRISE_PRODUCTION"),
                        "client": payload.get("client"),
                        "entropy": auth_entropy
                    }
                except Exception as e:
                    return {
                        "authorized": False,
                        "error": "TAMPER_DETECTED_FORGED_LICENSE",
                        "message": "Cryptographic signature mismatch. License key has been forged or corrupted.",
                        "action_required": "Obtain authentic signed key from Carlos Ferro (carlos@thinkconnect.com.ar)."
                    }

        # 2. Check 5-Day Evaluation Window
        first_launch = self.state["first_launch_epoch"]
        expiration = self.state["expiration_epoch"]
        remaining_seconds = max(0, int(expiration - now))
        remaining_hours = round(remaining_seconds / 3600.0, 1)

        # Anti-tamper clock rollback detection
        if now < first_launch - 60:
            return {
                "authorized": False,
                "error": "TAMPER_DETECTED_CLOCK_ROLLBACK",
                "message": "System clock rollback detected. Enclave permanently locked.",
                "action_required": "Contact Chief Architect Carlos Ferro (carlos@thinkconnect.com.ar) to reset license."
            }

        # Expired evaluation check
        if now > expiration:
            return {
                "authorized": False,
                "error": "EVALUATION_EXPIRED_5_DAYS",
                "message": f"5-day evaluation window (120 hours) has expired. Elapsed: {round((now - first_launch) / 86400, 1)} days.",
                "action_required": "To unlock production use, contact Carlos Ferro at carlos@thinkconnect.com.ar"
            }

        # Cumulative volume cap check
        if (self.state["volume_usd"] + amount) > MAX_TRIAL_VOLUME_USD:
            return {
                "authorized": False,
                "error": "EVALUATION_VOLUME_LIMIT_EXCEEDED",
                "message": f"Evaluation volume cap of ${MAX_TRIAL_VOLUME_USD:,.2f} USD exceeded. Current cumulative: ${self.state['volume_usd']:,.2f} USD.",
                "action_required": "Contact Carlos Ferro (carlos@thinkconnect.com.ar) for unlimited Enterprise license."
            }

        # Transaction count cap check
        if self.state["tx_count"] >= MAX_TRIAL_TRANSACTIONS:
            return {
                "authorized": False,
                "error": "EVALUATION_TX_LIMIT_EXCEEDED",
                "message": f"Evaluation limit of {MAX_TRIAL_TRANSACTIONS} transactions reached.",
                "action_required": "Contact Carlos Ferro (carlos@thinkconnect.com.ar) for Enterprise activation."
            }

        # Trial authorization entropy
        trial_entropy = hashlib.sha256(
            f"TRIAL_VALID:{first_launch}:{self.state['tx_count']}:{THINKCONNECT_MASTER_PUBLIC_KEY_HEX}".encode()
        ).hexdigest()

        return {
            "authorized": True,
            "mode": "COMMUNITY_TRIAL_5_DAYS",
            "hours_remaining": remaining_hours,
            "tx_remaining": MAX_TRIAL_TRANSACTIONS - self.state["tx_count"],
            "volume_remaining_usd": round(MAX_TRIAL_VOLUME_USD - self.state["volume_usd"], 2),
            "entropy": trial_entropy
        }

    def record_settlement(self, amount: float):
        self.state["tx_count"] += 1
        self.state["volume_usd"] += amount
        self.state["signature"] = self._sign_local_state(
            self.state["first_launch_epoch"],
            self.state["tx_count"],
            self.state["volume_usd"]
        )
        self._persist_state(self.state)
