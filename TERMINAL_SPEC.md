# Prediction Market Terminal — Product Specification & Roadmap

## 1. Product Definition

### What It Is
A unified **Prediction Market Intelligence & Trading Terminal** (the "Photon + Bloomberg" for prediction markets) that aggregates real-time data, order books, and trades across **Polymarket** and **Kalshi**. It provides traders with cross-platform arbitrage detection, on-chain whale tracking, automated copytrading, and quantitative strategy automation.

### The Core Problem It Solves
Prediction market traders currently suffer from:
1. **Fragmented Liquidity:** Navigating between Polymarket (crypto/USDC) and Kalshi (US fiat) across separate apps and browser tabs.
2. **Missing Analytics:** No institutional tooling to track profitable "smart money" wallets or mirror their trades in real-time.
3. **Hidden Arbitrage:** Large pricing discrepancies exist on the same real-world events across exchanges that retail traders cannot track manually.
4. **Lack of Strategy Automation:** Prediction markets lack native automated rule execution and algorithmic strategy tooling.

### What It Is NOT (Scope Guardrails)
* It is **NOT** a new prediction market exchange or clearinghouse. It is an analytics, intelligence, and execution layer built on top of existing exchanges.
* It does **NOT** custody user funds in Phase 1 (operates via non-custodial exchange API keys, local wallet signing, and paper trading).

---

## 2. The 4 Product Pillars & Feature Hierarchy

Features are prioritized by implementation order:
* **P0 (Critical MVP):** Must exist in the 30-day working product.
* **P1 (Core Expansion):** High-value features shipped immediately after MVP.
* **P2 (Scale & Monetization):** Advanced institutional and social features.

---

### Pillar 1: Market Intelligence & Unified Execution
*The core operating system of the terminal.*

* **P0 — Cross-Platform Market Browser:** Search and browse active events across Kalshi and Polymarket with normalized odds, volume, liquidity, and expiration dates.
* **P0 — Personal Portfolio & Trade Journal:** Unified tracking of user positions, cost basis, realized/unrealized PnL, with automated trade logs and note-taking.
* **P0 — Market Watchlists:** Custom tracking lists for user-selected events across categories (Economics, Politics, Culture, Tech, Science).
* **P1 — In-App Trading Execution:** Fast execution routing for Kalshi (REST API) and Polymarket (Polygon CLOB / wallet integration).
* **P1 — Risk Controls:** Automated slippage tolerance thresholds, max position sizing limits, and pre-trade safety confirmations.
* **P2 — Data Export:** One-click CSV and PDF reporting for historical tax, trade audit, and quantitative analysis.

---

### Pillar 2: Cross-Market Arbitrage & Edge Scanner
*The alpha engine that drives trader acquisition.*

* **P0 — Real-Time Discrepancy Scanner:** Live feed identifying matched events across Kalshi and Polymarket where probability divergence exceeds 5%.
* **P0 — Synthetic Risk-Free Arbitrage Detector:** Automatically flags instances where `Price(Kalshi YES) + Price(Polymarket NO) < $0.98`, guaranteeing positive expected value.
* **P1 — Instant Edge Alerts:** Push and Telegram notifications when an arbitrage spread or severe pricing anomaly opens.

---

### Pillar 3: On-Chain Whale Radar & Copytrading
*The retail engagement and viral growth engine.*

* **P0 — Polymarket Whale Tracker:** Scans Polygon blockchain transactions to identify and rank the most profitable prediction market wallets by win rate, total PnL, and volume.
* **P0 — Leaderboard & Trader Profiles:** Detailed breakdown of top traders, including category specialties (e.g. 85% win rate in Macro, 40% in Politics) and open positions.
* **P0 — Smart Money Alert Feed:** Real-time stream alerting when a top-tier whale opens a position over a configurable threshold (e.g., >$2,000).
* **P1 — Trader Comparison Tool:** Side-by-side metric comparison of two or more traders' historical performance, drawdown, and holding periods.
* **P1 — Automated Copytrading Bot (Simulated / Live):** Automatically allocate capital to mirror selected leader trades with proportional sizing and slippage caps.
* **P2 — Leader Marketplace:** Top traders can charge subscription fees or profit splits to let followers auto-copy their accounts.

---

### Pillar 4: Quant Strategy Studio & Automation
*The institutional edge and high-retention layer.*

* **P0 — Macro & Event Indicator Models:** Integrations with authoritative macroeconomic and statistical indicator feeds (e.g., inflation nowcasts, economic consensus data, polling aggregators).
* **P1 — No-Code Rule Builder:** Visual trigger engine: *"If [Indicator Probability] > X% and [Market Price] < Y¢, execute trade"*.
* **P1 — Automated Signal Notifications:** Alerts dispatched when external data feeds diverge significantly from market-implied odds.
* **P2 — Python Developer SDK (`predterm-sdk`):** Clean programmatic library allowing algorithmic traders to plug custom models into the terminal order router.

---

### Platform Foundation & UX
* **P0 — Dark Mode First UI:** Terminal aesthetic optimized for high-density information display.
* **P0 — Multi-Currency Display (USD & NGN):** Real-time conversion toggle for local purchasing power parity.
* **P1 — Streamlined Onboarding Flow:** Zero-friction wallet connect and demo balance initialization.
* **P2 — Referral Program:** Revenue-sharing mechanism for users inviting other traders.

---

## 3. Phase-by-Phase Roadmap (30-Day Launch Sprint)

Target Deadline: **October 31, 2026**

---

### Phase 1: Core Multi-Exchange Data Engine & Scanner (Days 1 – 7)
**Goal:** Build the unified backend data pipeline and live arbitrage scanner.
* [ ] Polymarket Gamma & CLOB API client (REST & WebSocket).
* [ ] Kalshi production market listener.
* [ ] Event normalization algorithm (matching identical events across both platforms).
* [ ] Real-time arbitrage calculator (`Kalshi YES + Poly NO < $1.00`).
* **Deliverable:** Working CLI tool and backend API streaming real-time cross-platform pricing discrepancies and arbitrage opportunities.

---

### Phase 2: Whale Radar & Trader Leaderboard (Days 8 – 14)
**Goal:** Index smart-money wallets and build the social trading analytics layer.
* [ ] Polymarket on-chain transaction parser (filtering for high-volume fills on Polygon).
* [ ] Whale Leaderboard database (Ranked by 30-day PnL, Win Rate, and Volume).
* [ ] Trader profile analytics (historical positions, trade sizes, PnL curve).
* [ ] Smart Money real-time trade alert webhook.
* **Deliverable:** Working API serving the top 100 trader profiles and live whale transaction feeds.

---

### Phase 3: Web Terminal UI & Paper Portfolio (Days 15 – 22)
**Goal:** Build the interactive browser-based terminal interface.
* [ ] Next.js + Tailwind CSS dark-mode dashboard.
* [ ] Live Market Browser with category filtering (Macro, Politics, Culture, Tech).
* [ ] Side-by-side Kalshi vs Polymarket odds viewer with Arb badges.
* [ ] Whale Leaderboard and Trader Profile pages.
* [ ] Local Paper Portfolio ($1,000 virtual balance) allowing users to paper-trade markets with one click.
* **Deliverable:** Live, usable web terminal running locally and on staging.

---

### Phase 4: Copy Engine & Alpha Launch (Days 23 – 30)
**Goal:** Connect the copytrading engine, complete integration tests, and launch to beta users.
* [ ] Automated paper copytrading (select a whale $\rightarrow$ mirror their new trades on paper portfolio).
* [ ] Macro/indicator model signals integrated into the terminal market view.
* [ ] Latency and data pipeline stress testing.
* [ ] Deploy to production hosting (Vercel / Cloud).
* [ ] Onboard 15–20 active prediction market beta testers.
* **Deliverable:** Public Version 1.0 Working Terminal.

---

## 4. Post-Launch Horizons (November & Beyond)

* **Horizon 2 (Weeks 5–8):** Real-money direct execution (Kalshi API key trade placement + Polymarket Web3 wallet signing).
* **Horizon 3 (Weeks 9–12):** Leader Marketplace (monetization via copytrading revenue share and pro subscriptions).
* **Horizon 4:** Multi-platform expansion to Betfair, PredictIt, and Robinhood event contracts.
