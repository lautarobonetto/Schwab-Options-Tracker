# Options Tracker for Schwab (Lightweight Edition)

## Project Overview

A specialized, self-hosted web application designed to track, group, and analyze advanced options strategies—specifically **Naked Puts** and **The Wheel**—using the Charles Schwab API.

This project is not affiliated with, funded, or in any way associated with Charles Schwab & Co., Inc.

## Key Problem Solved

Traditional broker interfaces treat "rolls" and stock assignments as separate, unrelated transactions. This obscures the true performance of a complex strategy over time.

This system solves that by implementing a custom **"Campaign Logic"** engine. It automatically groups these disparate trades into a single lifecycle, enabling traders to visualize the true **Accumulated Net Credit** and **Adjusted Breakeven** across the entire history of a position, regardless of how many times it has been rolled.

## Technical Highlights

Engineered for extreme resource efficiency to operate effectively within the **Google Cloud e2-micro Free Tier (1GB RAM)** limits.

* **Backend:** Python **FastAPI** (Async) for high-performance, non-blocking data processing.

* **Frontend:** **React + Vite** (Static SPA) for a responsive, modern UI without the overhead of a Node.js runtime.

* **Database:** **SQLite** for zero-overhead persistence and easy backups.

* **Deployment:** Single-container Docker architecture with Nginx reverse proxy for SSL termination.

## Core Features

1. **Campaign Grouping:** Automatically links `STO` (Sell to Open) and `BTC` (Buy to Close) trades into unified campaigns.

2. **The Wheel Tracking:** Tracks the full lifecycle from Short Put -> Assigned Stock -> Covered Calls.

3. **Real P&L:** Calculates profit based on the total net credit collected, not just the current open leg.

4. **Forensic Order Chain:** A Tastytrade-inspired timeline view to audit the history of every trade.

## Setup & Installation

Please refer to `AGENTS.md` and `docs/Technical_Architecture.md` for detailed instructions on how to deploy this system on your e2-micro instance.