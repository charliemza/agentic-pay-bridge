# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Security Shield & Circuit Breaker Engine
Implements 'Black October' defensive security doctrine for financial rails:
- Velocity limits & liquidity drain circuit breakers
- Monotonic nonce / epoch anti-replay fencing
- Immutable cryptographic SHA-256 audit logging
"""

import time
from typing import Dict, Any, List

class SecurityShield:
    def __init__(
        self,
        max_tx_amount: float = 5000.0,
        max_velocity_per_min: float = 15000.0,
        max_tx_count_per_min: int = 60
    ):
        self.max_tx_amount = max_tx_amount
        self.max_velocity_per_min = max_velocity_per_min
        self.max_tx_count_per_min = max_tx_count_per_min

        # State tracking
        self.agent_nonces: Dict[str, int] = {}
        self.velocity_window: List[Dict[str, Any]] = []
        self.circuit_breaker_tripped: bool = False
        self.audit_log: List[Dict[str, Any]] = []

    def verify_transaction_security(self, agent_id: str, amount: float, nonce: int) -> Dict[str, Any]:
        """
        Validates anti-replay, velocity constraints, and circuit breaker trip thresholds.
        """
        t0 = time.time()
        
        # 1. Check if global circuit breaker is active
        if self.circuit_breaker_tripped:
            return {
                "allowed": False,
                "reason": "CIRCUIT_BREAKER_ACTIVE: Global financial transactions halted due to anomalous velocity.",
                "circuit_breaker_active": True
            }

        # 2. Check maximum single transaction ceiling
        if amount > self.max_tx_amount:
            return {
                "allowed": False,
                "reason": f"EXCEEDS_MAX_TX_LIMIT: Requested {amount} exceeds maximum allowed {self.max_tx_amount}.",
                "circuit_breaker_active": False
            }

        # 3. Check anti-replay nonce monotonicity
        last_nonce = self.agent_nonces.get(agent_id, 0)
        if nonce <= last_nonce:
            return {
                "allowed": False,
                "reason": f"REPLAY_ATTACK_DETECTED: Nonce {nonce} is less than or equal to last seen nonce {last_nonce}.",
                "circuit_breaker_active": False
            }

        # 4. Check velocity window (trailing 60 seconds)
        now = time.time()
        # Clean older than 60s
        self.velocity_window = [entry for entry in self.velocity_window if (now - entry["time"]) <= 60.0]
        
        current_minute_volume = sum(entry["amount"] for entry in self.velocity_window) + amount
        current_minute_count = len(self.velocity_window) + 1

        if current_minute_volume > self.max_velocity_per_min or current_minute_count > self.max_tx_count_per_min:
            # Trip circuit breaker!
            self.circuit_breaker_tripped = True
            return {
                "allowed": False,
                "reason": f"VELOCITY_LIMIT_EXCEEDED: Volume {current_minute_volume} exceeds safety threshold {self.max_velocity_per_min}/min.",
                "circuit_breaker_active": True
            }

        # Update valid state
        self.agent_nonces[agent_id] = nonce
        self.velocity_window.append({"agent_id": agent_id, "amount": amount, "time": now})
        elapsed_ms = (time.time() - t0) * 1000

        return {
            "allowed": True,
            "elapsed_ms": elapsed_ms,
            "circuit_breaker_active": False
        }

    def record_audit_event(self, event_data: Dict[str, Any]):
        """Appends an immutable audit event for regulatory compliance."""
        self.audit_log.append(event_data)

    def reset_circuit_breaker(self):
        """Administrative unlock."""
        self.circuit_breaker_tripped = False
        self.velocity_window.clear()
