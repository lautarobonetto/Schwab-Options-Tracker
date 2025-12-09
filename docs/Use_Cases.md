# Use Case Document: Options Tracking System

This document breaks down the functional requirements into atomic units of work to facilitate incremental implementation.

**Suggested Development Strategy:**

1. Implement Module A (Backend Base).

2. Implement Module B (Business Logic and Tests).

3. Implement Module C (Detail UI).

4. Implement Module D (Dashboard UI).

## Module A: Connection and Data (Backend Core)

### UC-01: OAuth Authentication and Token Exchange

**Objective:** Obtain the first Access Token and Refresh Token from Schwab.

* **Actor:** System / User.

* **Input:** App Key, App Secret, Redirect URI (HTTPS).

* **Logic:**

  1. Generate Schwab authorization URL.

  2. Receive the `code` in the FastAPI callback.

  3. Exchange `code` for `access_token` and `refresh_token`.

  4. Save tokens encrypted in SQLite.

* **Acceptance Criteria:**

  * The user is redirected to Schwab login.

  * The database has a record in the `auth_tokens` table.

### UC-02: Automatic Token Refresh

**Objective:** Keep the session alive without manual intervention.

* **Actor:** System (Background Task).

* **Logic:**

  1. Before any API call, check if the token has expired (or expires in < 5 min).

  2. If expired, use the `refresh_token` to obtain a new one.

  3. Update the DB.

* **Acceptance Criteria:**

  * The system can make API calls 1 hour after the initial login without asking for credentials.

### UC-03: Transaction History Synchronization

**Objective:** Populate the local database with raw data.

* **Input:** Start date (e.g., 01-01-2023).

* **Logic:**

  1. Call Schwab endpoint `Get Transactions`.

  2. Filter irrelevant transactions (interest, minor dividends).

  3. Save to `raw_transactions` table (avoid duplicates using transaction ID).

* **Acceptance Criteria:**

  * `raw_transactions` table filled with JSON data.

  * No duplicates if the process is run twice.

## Module B: Strategy Engine (Business Logic)

*Note: This module must be developed together with Unit Tests (UC-20 - implied).*

### UC-04: Basic Grouping by Ticker

**Objective:** Organize transaction chaos.

* **Logic:**

  1. Read `raw_transactions`.

  2. Extract the underlying symbol (e.g., from "TSLA 230120P..." extract "TSLA").

  3. Group into JSON structure `{ "TSLA": [...], "AAPL": [...] }`.

* **Acceptance Criteria:**

  * Endpoint `/api/tickers` returns unique list of traded symbols.

### UC-05: Roll Detection (Naked Puts)

**Objective:** Identify when a position closes and another opens simultaneously.

* **Logic:**

  1. Within the same Ticker:

  2. Search for transaction pair: `BTC` (Buy to Close) and `STO` (Sell to Open).

  3. Condition: They occur within a time frame < 5 minutes (configurable).

  4. Action: Assign them the same `campaign_id`.

* **Acceptance Criteria:**

  * A roll from January to February is grouped under the same ID.

  * Unit test with mock data passes correctly.

### UC-06: "The Wheel" Detection (Assignment)

**Objective:** Link a sold Put with the received shares.

* **Logic:**

  1. Search for transaction type `ASSIGNMENT` or stock entry.

  2. Search for the previous `STO` Put that caused that assignment (same strike, expiration date close to assignment).

  3. Link both to the same `campaign_id`.

  4. Search for subsequent `STO` Calls (Covered Calls) and link them to the ID.

* **Acceptance Criteria:**

  * Sequence: Put -> Assignment -> Call stays under a single ID.

### UC-07: P&L and Adjusted Breakeven Calculation

**Objective:** Calculate the real metric of success.

* **Formula:**

  * `Net Credit` = Sum(STO Credits) - Sum(BTC Debits).

  * `Adjusted Breakeven (Put)` = Current Strike - Net Credit.

  * `Cost Basis (Wheel)` = Assignment Price - (Previous Put Credits + Call Credits).

* **Acceptance Criteria:**

  * The system returns the correct value for a scenario of 3 consecutive rolls.

### UC-08: Manual Override (Backend Drag & Drop)

**Objective:** Allow human correction when the algorithm fails.

* **Input:** `transaction_id`, `target_campaign_id`.

* **Logic:**

  1. Update the `campaign_id` of the specific transaction in the DB.

  2. Automatically recalculate metrics for the affected campaign.

* **Acceptance Criteria:**

  * Endpoint `POST /api/campaign/move-trade` works.

## Module C: Visualization (Order Chain)

### UC-09: Order Chain API (JSON)

**Objective:** Serve data ready to paint the Tastytrade-style UI.

* **Output JSON:** Chronologically ordered list (most recent at top).

  * Each item includes: `Date`, `Type` (STO/BTC), `P&L_link` (if closing), `Status` (Open/Closed).

* **Acceptance Criteria:**

  * The JSON correctly nests or references which trade closed which.

### UC-10: UI Component - Chronological List

**Objective:** Visualize the basic list.

* **Tech:** React + Tailwind.

* **Design:** Vertical cards.

* **Responsive:**

  * Desktop: Possible tabular view or wide list.

  * Mobile: Vertically stacked cards (Timeline).

* **Acceptance Criteria:**

  * All trades of the campaign are visible.

### UC-11: P&L per Link Visualization

**Objective:** See how much was earned/lost at each step.

* **UI Logic:**

  * Show Green/Red badge with the amount next to closing transactions (`BTC`).

  * Draw connector line (CSS border/SVG line) between the STO and its corresponding BTC.

* **Acceptance Criteria:**

  * It is visually obvious which operation closed which and the financial result of that pair.

## Module D: Dashboard and Charts

### UC-12: Ticker Cards (Dashboard Home)

**Objective:** High-level view.

* **Design:** Grid of cards.

* **Content:**

  * Symbol (e.g., SPY).

  * Total P&L of active Campaigns.

  * Risk Semaphore (UC-13).

* **Acceptance Criteria:**

  * All grouped positions are seen.

  * Click on card leads to "Order Chain".

### UC-13: Risk Semaphore (UI Logic)

**Objective:** Quick alert on iPhone.

* **Logic:**

  * Compare Current Price (Live Quote) vs Open Puts Strike.

  * Green: Price > Strike + 5%.

  * Yellow: Price between Strike and Strike + 5%.

  * Red: Price < Strike (ITM).

* **Acceptance Criteria:**

  * Colors change dynamically based on simulated market price.

### UC-14: Dynamic Payoff Chart

**Objective:** See "where I stand".

* **Tech:** Chart.js.

* **Data:**

  * X Axis: Stock price range.

  * Y Axis: Projected P&L.

  * Vertical Line 1: Current Price.

  * Vertical Line 2: Adjusted Breakeven (Calculated in UC-07).

* **Acceptance Criteria:**

  * The chart shows the extended profit zone thanks to accumulated credits.

  * Renders correctly inside a responsive container.

## Module Q: Quality (Testing)

### UC-15: Schwab API Mocking

**Objective:** Test without real money.

* **Action:** Create a fixture in Pytest that intercepts calls to `api.schwab.com` and returns predefined static JSONs.

* **Acceptance Criteria:**

  * Tests run without internet connection.

### UC-16: Financial Regression Tests

**Objective:** Ensure new code doesn't break old calculations.

* **Action:** Create a test dataset ("Golden Dataset") with a known complex Wheel scenario and verify that the final P&L result is exact to the penny.

* **Acceptance Criteria:**

  * `pytest` passes in green.