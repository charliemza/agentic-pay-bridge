# ⚡ AgenticPay Bridge — Turnkey Blockchain Payment Gateway & Agentic Settlement Core

[![License: Proprietary Evaluation](https://img.shields.io/badge/License-Proprietary%20Evaluation%20(5--Day%20Trial)-orange.svg)](LICENSE)
[![Security Enclave](https://img.shields.io/badge/Enclave-Cryptographic%20Time--Lock-red.svg)]()
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-emerald.svg)]()
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-teal.svg)]()
[![Tests](https://img.shields.io/badge/Tests-100%25%20Passing-brightgreen.svg)]()
[![Memory Footprint](https://img.shields.io/badge/Memory-%3C65MB-success.svg)]()
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)]()

> **English** | [Versión en Español abajo](#-versión-en-español)

**AgenticPay Bridge** is an institutional, ultra-lean (<65MB RAM) payment middleware designed for modern fintechs, neobanks, and autonomous AI agent runtimes. It connects traditional RESTful banking platforms to high-performance blockchain settlement rails (USDC/USDT on Base, Solana, and Polygon) in sub-800 milliseconds, reinforced with deterministic, four-layer defensive security controls (*Black October* doctrine).

> **Reference sandbox.** This public repository is an in-memory reference implementation for architecture review and API evaluation. Production blockchain adapters (on-chain USDC settlement), persistent ledger, per-client API keys and signed webhooks are available under license — contact `carlos@thinkconnect.com.ar`.

> **🔗 Live on-chain proof (Base Sepolia testnet).** Real USDC transfer executed by the licensed production adapter on 31/10/2026: **included in a block 0.59 s after broadcast** (block 52,790,352). Verify it yourself: [`0x91db9ca6…cbd30f4` on Basescan](https://sepolia.basescan.org/tx/0x91db9ca644eb8b6bf911cf3e482cdeec9cb619b5429c1742d07e43d6cdbd30f4). *Timing measured from broadcast to L2 inclusion; final settlement on Ethereum L1 takes a few additional minutes.*

---

## 🌟 Why AgenticPay Bridge?

1. **Sub-800ms Settlement:** Eliminates 48-hour SWIFT/ACH banking bottlenecks. Micro-payments and treasury sweeps settle with immediate block finality.
2. **Autonomous Agent-to-Agent (A2A) Commerce:** Enables AI agents, microservices, and bots to transfer funds programmatically with zero human friction (no card OTPs or SMS prompts).
3. **'Black October' Defensive Shield:**
   - **Velocity Circuit Breakers:** Automatically freezes transactions if liquidity drainage or infinite loops exceed safety ceilings ($/min).
   - **Monotonic Epoch Nonces:** 100% mathematical eradication of replay attacks.
   - **SHA-256 Verifiable Proofs:** Cryptographic audit trail for tax, compliance, and regulatory authorities (IRS 1099-DA, ARCA, EU DAC8).
4. **Zero-Bloat Architecture:** Pure Python 3.12 & FastAPI with zero Node.js / NPM dependencies.

---

## 🚀 Quickstart & Testing Options

### Option A: Self-Hosted in 60 Seconds (Local Docker)
```bash
git clone https://github.com/charliemza/agentic-pay-bridge.git
cd agentic-pay-bridge
docker compose up -d
```
The engine is now live and accepting requests at `http://localhost:8088`. Interactive Swagger API docs are available at `http://localhost:8088/docs`.

### Option B: Ephemeral Managed Sandbox On-Demand (Zero Installation)
If you are evaluating AgenticPay Bridge for your fintech or neobank and prefer not to deploy Docker locally during early architectural reviews, we can provision a **dedicated, isolated testing sandbox on our private infrastructure** for 72 hours with pre-funded testnet wallets and live API keys:
* Request access directly engineer-to-engineer: **`carlos@thinkconnect.com.ar`**
* Turnaround time: Sandbox provisioned and delivered within 15 minutes.

---

## 🏛️ Institutional Architecture & Technical Memorandum
For a rigorous mathematical breakdown of the settlement protocols, cryptographic threat models, and compliance alignment, read our formal whitepaper:
* [📄 Technical Architecture Memorandum (English)](TECHNICAL_MEMORANDUM.md)
* [📄 Memorando Técnico Ejecutivo (Español)](MEMORANDO_TECNICO_EJECUTIVO.md)

---

## ⚖️ Regulatory & Compliance Notice
AgenticPay Bridge is infrastructure software. It does not custody third-party funds and is not a money transmitter, exchange, or payment institution. Any party that operates it to move stablecoins or fiat on behalf of third parties is solely responsible for KYC/AML, sanctions screening, travel-rule obligations, and any licences required in its jurisdiction (e.g. MSB/MTL in the US, VASP/PSAV registration, MiCA in the EU). Nothing in this repository constitutes legal, tax, or financial advice.

---

## 📬 Engineer-to-Engineer Contact
We do not use sales reps, chatbots, or automated marketing funnels. If you are a fintech CTO, Lead Architect, or SRE exploring integration with proprietary banking cores:
* **Direct Engineering Contact:** Carlos Ferro — Principal Infrastructure & DevOps Engineer
* **Email:** `carlos@thinkconnect.com.ar`
* **Licensing:** Distributed under the ThinkConnect Proprietary Evaluation License (5-Day Time-Locked Enclave). Enterprise production keys available upon request.

---

# 🇪🇸 Versión en Español

**AgenticPay Bridge** es un middleware de pagos institucional y ultra-liviano (<65MB de RAM) diseñado para fintechs, neobancos y agentes autónomos de IA. Conecta los cores bancarios tradicionales mediante APIs REST con rieles de liquidación en blockchain de alta velocidad (USDC/USDT sobre Base, Solana y Polygon) en menos de 800 milisegundos, protegido por un blindaje de seguridad determinístico en 4 capas (*Doctrina Octubre Negro*).

> **Sandbox de referencia.** Este repositorio público es una implementación de referencia en memoria, pensada para revisión de arquitectura y evaluación de la API. Los adaptadores de producción para blockchain (liquidación real de USDC on-chain), el libro mayor persistente, las API keys por cliente y los webhooks firmados están disponibles bajo licencia — escribir a `carlos@thinkconnect.com.ar`.

> **🔗 Prueba en vivo en blockchain (red de prueba Base Sepolia).** Transferencia real de USDC ejecutada con el adaptador de producción licenciado el 31/10/2026: **incluida en un bloque 0,59 s después del envío** (bloque 52.790.352). Verificala vos mismo: [`0x91db9ca6…cbd30f4` en Basescan](https://sepolia.basescan.org/tx/0x91db9ca644eb8b6bf911cf3e482cdeec9cb619b5429c1742d07e43d6cdbd30f4). *Tiempo medido desde el envío hasta la inclusión en la red L2; el asentamiento final en Ethereum L1 demora unos minutos más.*

---

## 🎯 ¿Por qué AgenticPay Bridge?

1. **Liquidación en Sub-Segundo (<800ms):** Erradica las demoras de 48 a 72 horas de las transferencias tradicionales. Los fondos se liquidan de inmediato con confirmación en bloque.
2. **Comercio Autónomo Agente a Agente (A2A):** Permite que agentes de IA, bots y microservicios transfieran valor programáticamente sin fricción humana (sin tarjetas de crédito, OTPs por SMS ni pantallas interactivas).
3. **Blindaje Defensivo "Octubre Negro":**
   - **Disyuntores de Velocidad (Circuit Breakers):** Congela automáticamente transferencias si detecta bucles infinitos o intentos de vaciamiento de fondos que superen el umbral configurado ($/minuto).
   - **Nonces con Épocas Monotónicas:** Blindaje matemático contra ataques de repetición (*replay attacks*).
   - **Trazabilidad Criptográfica SHA-256:** Cada operación genera un comprobante inmutable apto para conciliación con fiscos y auditorías contables.
4. **Cero Dependencias Infladas:** Construido en Python 3.12 puro y FastAPI, sin librerías vulnerables de Node.js ni bloatware de NPM.

---

## ⚡ Opciones de Prueba y Despliegue

### Opción A: Auto-Alojado en 60 Segundos (Docker Local)
```bash
git clone https://github.com/charliemza/agentic-pay-bridge.git
cd agentic-pay-bridge
docker compose up -d
```
El motor queda corriendo en `http://localhost:8088`. La documentación interactiva de Swagger está en `http://localhost:8088/docs`.

### Opción B: Sandbox Administrado Temporal a Pedido (Cero Instalación)
Si estás evaluando la herramienta para una fintech o plataforma y preferís no instalar nada localmente durante la evaluación técnica, te provisionamos un **entorno sandbox dedicado y aislado en nuestros propios servidores** por 72 horas con wallets pre-cargadas y llaves de prueba listas:
* Solicitalo directamente ingeniero a ingeniero escribiendo a: **`carlos@thinkconnect.com.ar`**
* Plazo de entrega: Entorno montado y activo en menos de 15 minutos.

---

## ⚖️ Aviso Regulatorio y de Cumplimiento
AgenticPay Bridge es software de infraestructura. No custodia fondos de terceros ni actúa como transmisor de dinero, exchange o entidad de pago. Quien lo opere para mover stablecoins o dinero fíat por cuenta de terceros es el único responsable de KYC/AML, control de listas de sanciones, regla de viaje y de las licencias o registros que exija su jurisdicción (por ejemplo, registro de PSAV ante la CNV en Argentina, MSB/MTL en EE.UU. o MiCA en la UE). Nada en este repositorio constituye asesoramiento legal, impositivo ni financiero.

---

## 🤝 Contacto Directo de Ingeniería
No usamos representantes comerciales ni intermediarios. Si sos CTO, Arquitecto de Software o Lead de una fintech y querés evaluar la integración con tu core bancario propietario:
* **Responsable Técnico:** Carlos Ferro — Principal Infrastructure & DevOps Engineer
* **Email Directo:** `carlos@thinkconnect.com.ar`
* **Licenciamiento:** Distribuido bajo Licencia Propietaria de Evaluación (Enclave Temporal de 5 Días). Llaves maestras de producción enterprise disponibles a pedido.
