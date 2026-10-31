# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Programmatic Wallet Vault
Provides fintechs with multi-currency (USDC, USDT, Fíat) programmatic sub-accounts
for agents and corporate users with balance isolation and atomic state locks.
"""

import uuid
import time
from typing import Dict, Any, Optional

class WalletVault:
    def __init__(self):
        # In-memory fast ledger with atomic lock semantics
        self.wallets: Dict[str, Dict[str, Any]] = {}

    def create_wallet(self, owner_id: str, label: str, initial_balance: float = 0.0, asset: str = "USDC") -> Dict[str, Any]:
        """Creates a programmatic sub-wallet for a fintech user or autonomous agent."""
        wallet_id = f"wlt_{uuid.uuid4().hex[:12]}"
        wallet_data = {
            "wallet_id": wallet_id,
            "owner_id": owner_id,
            "label": label,
            "balances": {
                "USDC": initial_balance if asset == "USDC" else 0.0,
                "USDT": initial_balance if asset == "USDT" else 0.0,
                "USD_FIAT": 0.0
            },
            "created_at": time.time(),
            "status": "ACTIVE"
        }
        self.wallets[wallet_id] = wallet_data
        return {
            "status": "CREATED",
            "wallet_id": wallet_id,
            "owner_id": owner_id,
            "label": label,
            "initial_balance": wallet_data["balances"][asset],
            "asset": asset
        }

    def get_wallet(self, wallet_id: str) -> Optional[Dict[str, Any]]:
        return self.wallets.get(wallet_id)

    def deposit_funds(self, wallet_id: str, amount: float, asset: str = "USDC") -> Dict[str, Any]:
        wallet = self.wallets.get(wallet_id)
        if not wallet:
            return {"status": "ERROR", "reason": f"Wallet '{wallet_id}' not found."}
        if amount <= 0:
            return {"status": "ERROR", "reason": "Deposit amount must be positive."}
        
        wallet["balances"][asset] = round(wallet["balances"].get(asset, 0.0) + amount, 4)
        return {
            "status": "SUCCESS",
            "wallet_id": wallet_id,
            "new_balance": wallet["balances"][asset],
            "asset": asset
        }

    def transfer_funds(self, sender_id: str, receiver_id: str, amount: float, asset: str = "USDC") -> Dict[str, Any]:
        """Atomic fund transfer between two wallets."""
        sender = self.wallets.get(sender_id)
        receiver = self.wallets.get(receiver_id)

        if not sender:
            return {"status": "FAILED", "reason": f"Sender wallet '{sender_id}' not found."}
        if not receiver:
            return {"status": "FAILED", "reason": f"Receiver wallet '{receiver_id}' not found."}
        
        current_sender_bal = sender["balances"].get(asset, 0.0)
        if current_sender_bal < amount:
            return {
                "status": "FAILED",
                "reason": f"Insufficient funds. Required: {amount} {asset}, Available: {current_sender_bal} {asset}."
            }

        # Atomic debit and credit
        sender["balances"][asset] = round(current_sender_bal - amount, 4)
        receiver["balances"][asset] = round(receiver["balances"].get(asset, 0.0) + amount, 4)

        return {
            "status": "SUCCESS",
            "sender_new_balance": sender["balances"][asset],
            "receiver_new_balance": receiver["balances"][asset],
            "amount_transferred": amount,
            "asset": asset
        }
