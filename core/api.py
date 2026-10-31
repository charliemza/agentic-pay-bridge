# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - Core API Server
Ultra-lean FastAPI microservice (<60MB RAM footprint).
Exposes turnkey endpoints for fintech integration and agent-to-agent settlement.
"""

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from core.settlement_engine import SettlementEngine
from core.wallet_vault import WalletVault
from core.security_shield import SecurityShield

app = FastAPI(
    title="AgenticPay Bridge — Turnkey Fintech & A2A Payment Engine",
    version="1.0.0",
    description="High-performance blockchain settlement bridge and agent-to-agent payment gateway with Black October security shielding."
)

# Instantiate core singletons
vault = WalletVault()
shield = SecurityShield()
settlement = SettlementEngine(vault=vault, shield=shield)

# --- Pydantic Request Models ---
class CreateWalletRequest(BaseModel):
    owner_id: str = Field(..., example="agent_alpha_01")
    label: str = Field(..., example="Operating Treasury Wallet")
    initial_balance: float = Field(0.0, example=500.0)
    asset: str = Field("USDC", example="USDC")

class DepositRequest(BaseModel):
    wallet_id: str = Field(..., example="wlt_abc123")
    amount: float = Field(..., example=100.0)
    asset: str = Field("USDC", example="USDC")

class A2ATransferRequest(BaseModel):
    sender_wallet_id: str = Field(..., example="wlt_sender")
    receiver_wallet_id: str = Field(..., example="wlt_receiver")
    amount: float = Field(..., example=25.50)
    asset: str = Field("USDC", example="USDC")
    chain: str = Field("base", example="base")
    idempotency_key: Optional[str] = Field(None, example="idem_789xyz")
    nonce: Optional[int] = Field(None, example=1730380000)

# --- Endpoints ---
@app.get("/health")
def healthcheck():
    return {
        "status": "HEALTHY",
        "service": "AgenticPay Bridge Engine",
        "version": "1.0.0",
        "supported_chains": ["solana", "base", "polygon"],
        "supported_assets": ["USDC", "USDT"],
        "circuit_breaker_active": shield.circuit_breaker_tripped
    }

@app.post("/api/v1/wallets/create")
def create_wallet(req: CreateWalletRequest):
    res = vault.create_wallet(
        owner_id=req.owner_id,
        label=req.label,
        initial_balance=req.initial_balance,
        asset=req.asset
    )
    return res

@app.post("/api/v1/wallets/deposit")
def deposit_funds(req: DepositRequest):
    res = vault.deposit_funds(
        wallet_id=req.wallet_id,
        amount=req.amount,
        asset=req.asset
    )
    if res["status"] != "SUCCESS":
        raise HTTPException(status_code=400, detail=res["reason"])
    return res

@app.get("/api/v1/wallets/{wallet_id}")
def get_wallet(wallet_id: str):
    w = vault.get_wallet(wallet_id)
    if not w:
        raise HTTPException(status_code=404, detail=f"Wallet '{wallet_id}' not found.")
    return w

@app.post("/api/v1/settlement/transfer")
def execute_transfer(req: A2ATransferRequest):
    res = settlement.execute_a2a_settlement(
        sender_agent_id=req.sender_wallet_id,
        receiver_agent_id=req.receiver_wallet_id,
        amount=req.amount,
        asset=req.asset,
        chain=req.chain,
        idempotency_key=req.idempotency_key,
        nonce=req.nonce
    )
    if res["status"] == "BLOCKED_BY_SHIELD":
        raise HTTPException(status_code=403, detail=res)
    elif res["status"] in ["REJECTED", "FAILED"]:
        raise HTTPException(status_code=400, detail=res)
    return res

@app.get("/api/v1/audit/trail")
def get_audit_trail(limit: int = 50):
    return {
        "total_records": len(shield.audit_log),
        "records": shield.audit_log[-limit:]
    }
