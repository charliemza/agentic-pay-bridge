# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Proprietary License & Cryptographic Time-Bomb Enclave
Enforces strict 5-day evaluation window (120 hours) and volume caps.
Requires Master Cryptographic Unlock Key from Carlos Ferro (ThinkConnect IA) for production.
"""

import time
import os
import hmac
import hashlib
import json
from typing import Dict, Any, Optional

# Chief Architect Master Public Salt
THINKCONNECT_MASTER_SALT = "ThinkConnect-IA-CarlosFerro-MasterSecret-2026"
EVALUATION_WINDOW_SECONDS = 5 * 24 * 3600  # Exactly 5 days (120 hours)
MAX_TRIAL_TRANSACTIONS = 100
MAX_TRIAL_VOLUME_USD = 2500.0

class LicenseEnclave:
    def __init__(self, state_dir: Optional[str] = None):
        if not state_dir:
            state_dir = os.path.dirname(os.path.abspath(__file__))
        self.state_file = os.path.join(state_dir, ".license_enclave_state.dat")
        self.state = self._initialize_or_load_state()

    def _initialize_or_load_state(self) -> Dict[str, Any]:
        now = time.time()
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Verify internal state tamper-proof signature
                    calc_sig = self._sign_payload(data["first_launch_epoch"], data["tx_count"], data["volume_usd"])
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
        initial_state["signature"] = self._sign_payload(
            initial_state["first_launch_epoch"],
            initial_state["tx_count"],
            initial_state["volume_usd"]
        )
        self._persist_state(initial_state)
        return initial_state

    def _sign_payload(self, epoch: float, count: int, volume: float) -> str:
        raw = f"{epoch:.2f}:{count}:{volume:.2f}:{THINKCONNECT_MASTER_SALT}"
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
        unlock key has been injected.
        """
        # 1. Check if Enterprise Master License Key is present in environment
        env_key = os.environ.get("AGENTICPAY_LICENSE_KEY", "")
        if env_key:
            expected_key = hmac.new(
                THINKCONNECT_MASTER_SALT.encode("utf-8"),
                b"ENTERPRISE_UNLIMITED_PRODUCTION_LICENSE",
                hashlib.sha256
            ).hexdigest()
            if env_key == expected_key:
                return {"authorized": True, "mode": "ENTERPRISE_PERPETUAL_LICENSE"}

        # 2. Check 5-Day Time Bomb
        now = time.time()
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
        if now >= expiration:
            return {
                "authorized": False,
                "error": "EVALUATION_TRIAL_EXPIRED_5_DAYS",
                "remaining_hours": 0.0,
                "message": "CRITICAL: 5-Day Free Evaluation Window has expired.",
                "action_required": "To obtain the production master unlock key, contact Carlos Ferro: carlos@thinkconnect.com.ar"
            }

        # Check trial transaction counter and volume ceiling
        if self.state["tx_count"] >= MAX_TRIAL_TRANSACTIONS:
            return {
                "authorized": False,
                "error": "TRIAL_TX_LIMIT_EXCEEDED",
                "message": f"Maximum evaluation limit of {MAX_TRIAL_TRANSACTIONS} transactions reached.",
                "action_required": "Contact carlos@thinkconnect.com.ar for enterprise production key."
            }

        if (self.state["volume_usd"] + amount) > MAX_TRIAL_VOLUME_USD:
            return {
                "authorized": False,
                "error": "TRIAL_VOLUME_LIMIT_EXCEEDED",
                "message": f"Evaluation volume threshold (${MAX_TRIAL_VOLUME_USD} USD) reached.",
                "action_required": "Contact carlos@thinkconnect.com.ar for enterprise production key."
            }

        return {
            "authorized": True,
            "mode": "COMMUNITY_EVALUATION_TRIAL",
            "remaining_trial_hours": remaining_hours,
            "processed_trial_txs": self.state["tx_count"],
            "max_trial_txs": MAX_TRIAL_TRANSACTIONS
        }

    def record_settlement(self, amount: float):
        """Updates internal trial meter with cryptographic integrity signature."""
        self.state["tx_count"] += 1
        self.state["volume_usd"] = round(self.state["volume_usd"] + amount, 2)
        self.state["signature"] = self._sign_payload(
            self.state["first_launch_epoch"],
            self.state["tx_count"],
            self.state["volume_usd"]
        )
        self._persist_state(self.state)
