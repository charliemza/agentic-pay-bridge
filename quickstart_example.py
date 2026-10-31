#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AgenticPay Bridge - 30-Second Quickstart Example
Demonstrates wallet creation, deposit, and autonomous A2A settlement.
"""

import urllib.request
import json
import time

BASE_URL = "http://localhost:8088"

def post(endpoint, data):
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def main():
    print("[*] Testing AgenticPay Bridge Engine...")

    # 1. Healthcheck
    with urllib.request.urlopen(f"{BASE_URL}/health") as resp:
        health = json.loads(resp.read().decode("utf-8"))
        print(f"[+] Engine Status: {health['status']} | Chains: {health['supported_chains']}")

    # 2. Create Sender Wallet
    w_sender = post("/api/v1/wallets/create", {
        "owner_id": "fintech_client_01",
        "label": "AI Trading Desk",
        "initial_balance": 1500.0,
        "asset": "USDC"
    })
    print(f"[+] Sender Wallet Created: {w_sender['wallet_id']} (Balance: {w_sender['initial_balance']} USDC)")

    # 3. Create Receiver Wallet
    w_receiver = post("/api/v1/wallets/create", {
        "owner_id": "service_agent_omega",
        "label": "Cloud GPU Provider",
        "initial_balance": 0.0,
        "asset": "USDC"
    })
    print(f"[+] Receiver Wallet Created: {w_receiver['wallet_id']}")

    # 4. Execute Autonomous A2A Settlement
    tx = post("/api/v1/settlement/transfer", {
        "sender_wallet_id": w_sender["wallet_id"],
        "receiver_wallet_id": w_receiver["wallet_id"],
        "amount": 42.50,
        "asset": "USDC",
        "chain": "base",
        "nonce": int(time.time() * 1000)
    })
    print(f"[+] Autonomous A2A Transfer Settled!")
    print(f"    - Tx ID: {tx['tx_id']}")
    print(f"    - SHA-256 Proof: {tx['tx_hash']}")
    print(f"    - Latency: {tx['settlement_latency_ms']} ms")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[-] Could not connect to {BASE_URL}. Ensure the engine is running (`docker compose up -d`). Error: {e}")
