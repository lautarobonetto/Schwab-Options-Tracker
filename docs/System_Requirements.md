# Functional Definition Document: Options Tracking System (Schwab API)

## 1. Overview

The objective is to develop a web application that consumes the Charles Schwab API to track, group, and visualize the performance of advanced options strategies.
The system must support two main workflows:

1. **Naked Puts & Rolling:** Management of defensive positions through rolling for net credit.

2. **The Wheel Strategy:** Management of the complete cycle (Put Sale -> Stock Assignment -> Covered Calls).

The core of the system is the ability to manage the lifecycle of a "Campaign," consolidating multiple operations and underlying stock holdings to calculate real P&L and adjusted Cost Basis.

## 2. Functional Modules

### Module A: Connection and Authentication (Schwab API)

This module is the gateway and must handle security and session management.

1. **OAuth 2.0 Authentication:**

   * Implement Schwab's "App Authorization" flow.

   * Automatic management of the `Refresh Token` to keep the session alive without constant logins.

2. **Account Selector:**

   * Support for multiple accounts and a consolidated view.

3. **Data Synchronization (Sync Engine):**

   * *Historical:* Download of transactions and **stock positions** (necessary for Covered Calls).

   * *Intraday:* Polling of prices for options and underlyings.

4. **User Access Control:**

   * **Web Interface Security:** Access to the application dashboard is restricted via Basic Authentication (Nginx). The user must authenticate before accessing any UI or API endpoint from the browser.

### Module B: Grouping Logic and Strategies ("Campaign Logic")

**This is the heart of the system.** It must organize the chaos of individual transactions into a clear hierarchical structure.

4. **Data Hierarchy:**

   * **Level 1: Underlying (Ticker):** Everything is grouped first by the symbol (e.g., SPY, TSLA).

   * **Level 2: Campaign/Strategy:** Within a Ticker, related operations are grouped.

   * **Level 3: Individual Trades:** Atomic operations (Buy, Sell, Assign).

5. **Strategy Detection Algorithm:**

   * **Roll Detection:** Identify simultaneous closing and opening in the same Ticker.

   * **"The Wheel" Detection:** Link Put -> Assignment -> Covered Call.

6. **Advanced Metrics Calculation:**

   * *Accumulated Net Credit:* Sum of all rollings.

   * *Adjusted Breakeven:* Strike - Total Credits.

   * *Real Stock Cost Basis:* Original assignment price - Accumulated premiums.

7. **Manual Management:** Interface to correct automatic groupings.

### Module C: Order Chain Visualization

**Objective:** Replicate the grouping and chronology functionality of **Tastytrade Order Chains** for P&L auditing.

 8. **Chronological Transaction Chain:**

    * Display a clear chronological sequence of all "links" in the strategy. The priority is to understand the temporal sequence of events, regardless of whether the layout is vertical or horizontal.

    * Each block or row must represent a trade event (STO, BTC, BTO, STC).

 9. **Visual Pair Connection (Links):**

    * Visually group the opening operation with its corresponding closing.

    * **P&L Indicator per Link:** To the right of each closed pair, clearly show the realized Profit/Loss of *that* specific transaction (e.g., "BTC Put Jan 20" vs "STO Put Jan 20" = +$150).

    * **Color Code:** Green for profit (Credit > Debit), Red for loss (Debit > Credit).

10. **Campaign Summary Header:**

    * At the top of the chain, show the accumulated **Total P&L** of the entire history.

    * Show the **Avg Trade Price** or Average Credit received.

    * Chain Status: "Open" (active position) or "Closed" (finalized history).

11. **Execution Detail:**

    * In each order card/row show: Date/Time, Quantity, Instrument (Call/Put), Strike, Expiration, and Execution Price.

    * Clear action labels: **STO** (Sell to Open), **BTC** (Buy to Close), **Assigned**.

### Module D: Performance and Risk Dashboard

12. **Main View by Ticker (Grouping):**

    * The Dashboard should not list loose options, but cards per Ticker (e.g., A large card for "SPY").

    * Inside the card, break down active strategies (e.g., "2 Naked Puts", "1 Covered Call").

13. **Dynamic Payoff Chart (Dual Support):**

    * **Naked Put Mode:** Shows downside risk and profit limited to credit. *Adjusted Breakeven* line.

    * **Covered Call Mode:** Shows stock risk profile, but with the profit "ceiling" defined by the sold Call and the "floor" cushioned by collected premiums.

14. **Status Semaphore:**

    * Green: Winning position / Safe OTM.

    * Yellow: Price approaching Strike / Mild ITM.

    * Red: Deep ITM / Risk of imminent unwanted assignment.

15. **Unified Expiration Calendar:**

    * Chronological view of when both Puts and Calls expire.

## 3. Technical Requirements (Optimized for e2-micro/Free Tier)

This architecture is designed to run with **1 GB of RAM** and minimize deployment complexity.

### A. Technology Stack (Lightweight)

* **Backend:** **Python with FastAPI**.

  * *Reason:* Extremely fast, low memory consumption compared to traditional frameworks, and excellent asynchronous support for Schwab API calls. Robust financial libraries (Pandas/Numpy).

* **Frontend:** **React (Vite) - SPA (Single Page Application)**.

  * *Reason:* Compiles to static HTML/JS/CSS files. Does not require a Node.js server running in production, saving ~200MB of RAM.

* **Database:** **SQLite**.

  * *Reason:* File-based database. Zero RAM consumption when idle, no heavy server processes. Ideal for a personal tool with <100,000 transactions.

  * *Persistence:* The `.db` file is saved in a Docker persistent volume.

### B. Infrastructure and Deployment

* **Containerization:** **Docker & Docker Compose**.

  * A single container for the Backend (Python) which also serves the static Frontend files (React).

* **Web Integration:** **Nginx + Certbot (Existing)**.

  * The system must be exposed on a local port (e.g., 8000) and provide the `server` block configuration so that the existing Nginx acts as a Reverse Proxy (`proxy_pass`).

  * This satisfies Schwab's HTTPS requirement without consuming additional resources.

### C. Schwab API Configuration

* **App Key & Secret:** Managed via environment variables (`.env`) on the server. Never hardcoded.

* **Token Storage:** Access and refresh tokens are stored encrypted in the SQLite database.

### D. Memory Optimization (e2-micro)

* Enable **Swap Memory** on Linux (2GB swap file) to prevent system crashes during data processing peaks.

### E. Responsive Design (Mobile Support - iPhone)

* **CSS Framework:** Use **Tailwind CSS**. Allows creating adaptive designs quickly without heavy CSS.

* **Mobile-First Strategy:**

  * **Order Chain:** The design must adapt fluidly. On desktop, a table or expanded timeline layout can be used, while on mobile it must collapse to a readable view (cards or list) without breaking the chronological sequence.

  * **Charts:** Payoff charts must automatically adjust their size to the device width (`responsive container`).

  * **Touch Interaction:** Buttons and click areas (tap targets) of at least 44x44px to facilitate finger use.

## 4. Quality Strategy and Automated Testing

To ensure system reliability without constant manual intervention, Antigravity must implement the following automated testing strategy:

### A. Financial Logic Unit Tests (Backend - Pytest)

Since a calculation error can lead to wrong financial decisions, this is the most critical level.

* **Financial Math Tests:** Create specific tests for `Net Credit`, `Adjusted Breakeven`, and `Yield on Cost` calculation functions.

  * *Example:* "Given a roll from Strike 100 to 95 with a net credit of $2.00, verify that the Breakeven is 93."

* **Grouping Algorithm Tests:** Simulate a list of disordered JSON transactions and verify that the algorithm correctly groups them into the expected Campaign.

* **Schwab API Mocking:** Use mocking libraries to simulate Schwab API responses. **Never** depend on the real connection to Schwab to run tests (avoids authentication issues in CI/CD).

### B. Integration Tests (FastAPI + SQLite In-Memory)

* **API Endpoints:** Verify that REST endpoints return correct status codes (200, 400, 500) and data structures.

* **Persistence:** Use an in-memory SQLite database (`:memory:`) during tests to ensure transactions are saved and retrieved correctly without affecting the real database.

### C. Data Validation (Pydantic)

* Implement strict `Pydantic` models for all Schwab API responses. If Schwab's API changes its format, the system must fail in a controlled manner and alert, rather than silently processing corrupt data.

### D. UI/Component Tests (Frontend - Vitest)

* **Chain Rendering:** Verify that the `OrderChain` component renders the correct number of "links" based on test data.

* **Semaphore Logic:** Test that the status indicator component shows "Red" if current price < put strike, and "Green" otherwise.

## 5. User Stories

1. *"As a trader, I want to see all my **SPY** positions grouped in a single card, seeing how much I have earned in total by adding stock appreciation and Covered Call premiums."*

2. *"As a user, I want to see the history of my trades in 'TSLA' just like Tastytrade does, clearly seeing that I closed my January Put with a $200 loss, but opened the February one for $500, resulting in a positive total P&L."*

3. *"As a trader, I want to quickly check from my iPhone if my Naked Puts are in danger (ITM) using a semaphore-type color system."*