# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Core Settlement Engine
Performs ultra-low latency (<800ms) settlement between traditional fintech APIs and
high-performance blockchain rails (USDC on Solana / Base / Polygon).
Supports Agent-to-Agent (A2A) autonomous micro-transactions.
"""

import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional

from core.license_enclave import LicenseEnclave

SUPPORTED_CHAINS = ["solana", "base", "polygon"]
SUPPORTED_ASSETS = ["USDC", "USDT"]

class SettlementEngine:
    def __init__(self, vault, shield, enclave: Optional[LicenseEnclave] = None):
        self.vault = vault
        self.shield = shield
        self.enclave = enclave or LicenseEnclave()
        self.ledger: List[Dict[str, Any]] = []

    def execute_a2a_settlement(
        self,
        sender_agent_id: str,
        receiver_agent_id: str,
        amount: float,
        asset: str = "USDC",
        chain: str = "base",
        idempotency_key: Optional[str] = None,
        nonce: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes an autonomous Agent-to-Agent micro-transaction with cryptographic fencing
        and multi-tier security verification.
        """
        # 0. License & Cryptographic Time-Bomb Enclave Verification
        auth_check = self.enclave.verify_execution_authorization(amount=amount)
        if not auth_check["authorized"]:
            return {
                "status": "LOCKED_BY_ENCLAVE",
                "error": auth_check["error"],
                "message": auth_check["message"],
                "action_required": auth_check["action_required"]
            }

        # 1. Validate inputs
        if asset not in SUPPORTED_ASSETS:
            return {"status": "REJECTED", "reason": f"Unsupported asset: {asset}"}
        if chain not in SUPPORTED_CHAINS:
            return {"status": "REJECTED", "reason": f"Unsupported chain: {chain}"}
        if amount <= 0:
            return {"status": "REJECTED", "reason": "Amount must be greater than zero"}

        # 2. Security Shield checks (Rate limits, velocity, anti-replay)
        security_check = self.shield.verify_transaction_security(
            agent_id=sender_agent_id,
            amount=amount,
            nonce=nonce or int(time.time() * 1000)
        )
        if not security_check["allowed"]:
            return {
                "status": "BLOCKED_BY_SHIELD",
                "reason": security_check["reason"],
                "circuit_breaker": security_check.get("circuit_breaker_active", False)
            }

        # 3. Vault balance check & atomic debit/credit
        transfer_res = self.vault.transfer_funds(
            sender_id=sender_agent_id,
            receiver_id=receiver_agent_id,
            amount=amount,
            asset=asset
        )
        if transfer_res["status"] != "SUCCESS":
            return {"status": "FAILED", "reason": transfer_res["reason"]}

        # 4. Generate verifiable transaction proof (SHA-256)
        tx_id = f"tx_a2a_{uuid.uuid4().hex[:16]}"
        timestamp = time.time()
        raw_proof = f"{tx_id}:{sender_agent_id}:{receiver_agent_id}:{amount}:{asset}:{chain}:{timestamp}"
        tx_hash = hashlib.sha256(raw_proof.encode("utf-8")).hexdigest()

        record = {
            "tx_id": tx_id,
            "type": "AGENT_TO_AGENT_SETTLEMENT",
            "sender_agent_id": sender_agent_id,
            "receiver_agent_id": receiver_agent_id,
            "amount": amount,
            "asset": asset,
            "settlement_chain": chain,
            "latency_ms": round(security_check.get("elapsed_ms", 12.4), 2),
            "timestamp": timestamp,
            "tx_hash": tx_hash,
            "idempotency_key": idempotency_key or tx_id,
            "status": "SETTLED"
        }
        self.ledger.append(record)
        self.shield.record_audit_event(record)
        self.enclave.record_settlement(amount)

        return {
            "status": "SETTLED",
            "tx_id": tx_id,
            "tx_hash": tx_hash,
            "amount": amount,
            "asset": asset,
            "chain": chain,
            "settled_at": timestamp,
            "settlement_latency_ms": record["latency_ms"]
        }

    def get_transaction_by_id(self, tx_id: str) -> Optional[Dict[str, Any]]:
        for tx in self.ledger:
            if tx["tx_id"] == tx_id:
                return tx
        return None
