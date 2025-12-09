# Technical Architecture Document: Schwab Options Tracker

**Version:** 1.0

**Objective:** Technical implementation guide for the development of the Options Tracking System.

**Critical Constraint:** The system must operate on a **Google Cloud e2-micro instance (2 vCPU, 1 GB RAM)**. Memory efficiency is priority #1.

## Related Documentation

For detailed specifications, please refer to the following documents in the `docs/` folder:

*   **Requirements:** [docs/System_Requirements.md](docs/System_Requirements.md)
*   **Architecture:** [docs/Technical_Architecture.md](docs/Technical_Architecture.md)
*   **Use Cases:** [docs/Use_Cases.md](docs/Use_Cases.md)

## 1. Technology Stack

### 1.1 Backend (API & Logic)

* **Language:** Python 3.11+
* **Framework:** **FastAPI** (Chosen for asynchronous performance and low overhead).
* **ASGI Server:** **Uvicorn** (Configured with `workers=1` to limit RAM consumption).
* **Dependency Management:** `poetry` or `pip` with `requirements.txt`.
* **Key Libraries:**
  * `httpx`: Asynchronous HTTP client to consume the Schwab API.
  * `pandas`: Financial data processing and grouping.
  * `sqlalchemy`: ORM (using Core for complex queries if necessary).
  * `pydantic`: Strict data validation.
  * `pytest`: Testing suite.

### 1.2 Frontend (UI)

* **Framework:** **React 18+**
* **Build Tool:** **Vite** (Compiles to static files, no Node server at runtime).
* **Styles:** **Tailwind CSS** (Utility-first, responsive).
* **State:** React Context API + Hooks (Avoid Redux to maintain simplicity).
* **Charts:** `chart.js` + `react-chartjs-2`.
* **Icons:** `lucide-react`.

### 1.3 Persistence (Data)

* **Engine:** **SQLite** (Local `.db` file).
* **Reason:** Zero RAM consumption at rest. Ideal for <100k transactions.
* **Location:** Docker persistent volume `/data/schwab_tracker.db`.

### 1.4 Infrastructure

* **Containers:** **Docker** (Multi-stage build to reduce image size).
* **Orchestration:** **Docker Compose** (Single service for app, volumes).
* **Reverse Proxy:** **Nginx** (Installed on host, handles SSL and `proxy_pass` to the container).

## 2. Architecture Diagram (Data Flow)

```
[User (Browser/iPhone)] -->|HTTPS (443)| [Nginx (Host)]
[Nginx] -->|Proxy Pass (8000)| [Docker Container]

Inside Docker Container:
  [FastAPI Backend] -->|Serves| [React Static Files]
  [FastAPI Backend] -->|Async Calls| [Charles Schwab API]
  [FastAPI Backend] -->|Read/Write| [SQLite DB]
```
## 3. Project Structure (Monorepo)

To facilitate deployment on a single instance, we will use a unified structure where the Backend serves the Frontend static files.

```
/schwab-tracker-app
├── /backend
│   ├── /app
│   │   ├── /api
│   │   │   ├── /endpoints      # Routes (auth.py, data.py, campaigns.py)
│   │   │   └── api.py          # Main Router
│   │   ├── /core               # Config (config.py, security.py)
│   │   ├── /db                 # Database (session.py, base.py)
│   │   ├── /models             # SQL Alchemy Models (user.py, transaction.py)
│   │   ├── /schemas            # Pydantic Models (transaction_schema.py)
│   │   ├── /services           # Business Logic (schwab_client.py, grouping_algo.py)
│   │   └── main.py             # FastAPI Entrypoint
│   ├── /tests                  # Pytest folder
│   ├── requirements.txt
│   └── Dockerfile              # Unified Dockerfile
├── /frontend
│   ├── /src
│   │   ├── /components         # Reusable UI (Card, Button, OrderChain)
│   │   ├── /pages              # Views (Dashboard, Settings, ChainDetail)
│   │   ├── /services           # Backend Calls (api.js)
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── .env.example
```

## 4. Database Design (Schema)

Simplified relational schema for SQLite.

### Main Tables

1. **`auth_tokens`**
   * `id` (PK)
   * `access_token` (Text, Encrypted)
   * `refresh_token` (Text, Encrypted)
   * `expires_at` (Datetime)

2. **`raw_transactions`** (Schwab Mirror)
   * `id` (PK, Schwab Activity ID)
   * `date` (Datetime)
   * `symbol` (String, Indexed)
   * `description` (String)
   * `quantity` (Float)
   * `price` (Float)
   * `amount` (Float)
   * `type` (String: TRADE, JOURNAL, ASSIGN)

3. **`campaigns`** (Logical Grouping)
   * `id` (PK, UUID)
   * `ticker` (String, Indexed)
   * `status` (Enum: OPEN, CLOSED)
   * `strategy_type` (Enum: NAKED_PUT, WHEEL, COVERED_CALL)
   * `start_date` (Datetime)
   * `closed_date` (Datetime, Nullable)
   * `total_pnl` (Float, Computed)

4. **`campaign_trades`** (Pivot Table)
   * `campaign_id` (FK -> campaigns.id)
   * `transaction_id` (FK -> raw_transactions.id)
   * `role` (Enum: OPENING, CLOSING, ADJUSTMENT, ASSIGNMENT)
   * `link_id` (UUID, Nullable - To link specific STO-BTC pairs)

## 5. API Design (Key Endpoints)

### Auth
* `GET /api/auth/login`: Redirects to Schwab OAuth.
* `GET /api/auth/callback`: Receives `code`, exchanges tokens, and saves to DB.

### Data Sync
* `POST /api/sync/history`: Triggers background task to download history.
* `GET /api/sync/status`: Synchronization status.

### Campaigns (Core Logic)
* `GET /api/campaigns`: Lists campaigns grouped by Ticker (Dashboard).
* `GET /api/campaigns/{id}`: Full detail (Order Chain data).
* `POST /api/campaigns/regroup`: Moves a transaction from one campaign to another (Drag & Drop).

## 6. Algorithm Implementation Strategy (Module B)

### Roll Detection Algorithm (Pseudo-code)
To be implemented in `backend/app/services/grouping_algo.py`:

1. Get all transactions for a Ticker ordered by date.
2. Iterate over the list.
3. If we find a `BTC` (Buy to Close):
   * Check within a time window (e.g., +/- 10 mins) if an `STO` (Sell to Open) exists.
   * If it exists: It is a Roll.
     * Create/Update `Campaign`.
     * Mark `BTC` as closing the previous trade.
     * Mark `STO` as the new link in the same campaign.
   * If it does not exist: It is a definitive close. Mark Campaign as `CLOSED`.

### "The Wheel" Algorithm
1. If transaction == `ASSIGNMENT`:
   * Find previous `STO` Put with the same Strike/Expiration.
   * Extend its `Campaign` to include the assignment (we now own shares).
2. If transaction == `STO` Call (Covered Call):
   * If we have inventory of assigned shares in that campaign, link this Call to the existing campaign.

## 7. Deployment Configuration (Docker)

### Unified Dockerfile (Multi-Stage)
This approach drastically reduces final size and memory usage.

```dockerfile
# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build  # Generates /dist folder

# Stage 2: Python Runtime
FROM python:3.11-slim
WORKDIR /app
# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy Backend Code
COPY backend/ .
# Copy Built Frontend Assets from Stage 1
COPY --from=frontend-build /app/frontend/dist /app/static

# Env Vars defaults
ENV SQLITE_DB_PATH=/data/schwab.db

# Security: Run as non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Command: Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Configuration (Host)
Snippet to add to your existing configuration:

```nginx
server {
    server_name yourserver.com;
    # ... SSL config (Certbot) ...

    # Security Headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';";

    location / {
        # Basic Auth
        auth_basic "Restricted Access";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass http://localhost:8000; # Points to the Docker container
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # Enable Websockets if required in the future
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 8. Security and Secrets

1. **Token Encryption:**
   * Use the `cryptography` (Fernet) library in Python to encrypt Access/Refresh tokens before saving them to SQLite.
   * The encryption key (`ENCRYPTION_KEY`) must be in the `.env` file.
2. **Environment Variables (.env):**
   * `SCHWAB_APP_KEY`
   * `SCHWAB_APP_SECRET`
   * `ENCRYPTION_KEY`
   * `REDIRECT_URI` (Must match exactly what is registered in the Schwab Developer Portal).
3. **Application Access Control:**
   * Nginx Basic Auth is enabled to restrict public access to the dashboard.
   * `htpasswd` file must be generated on the host machine.
4. **Container Security:**
   * The Docker container runs as a non-root user (`appuser`) to minimize privilege escalation risks.
5. **Secrets File Permissions:**
   * Ensure `.env` file has restricted permissions (`chmod 600`) as it contains sensitive keys.

## 9. Next Steps for Antigravity

To start development, instruct Antigravity in this order:

1. **Setup:** "Create the `backend` and `frontend` folder structure according to the architecture document and generate the base `docker-compose.yml`."
2. **Backend Core:** "Implement the SQLAlchemy models in `backend/app/models` based on the database design."
3. **Logic:** "Implement the Schwab client in `backend/app/services/schwab_client.py` using `httpx`."