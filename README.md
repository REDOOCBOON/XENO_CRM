# XenoPilot - AI Marketing Operating System

XenoPilot is an AI-native CRM and Marketing Operating System built as a production-grade submission for Xeno's Engineering Assignment.

Instead of traditional manual list-pulling and ad-hoc campaign creation, XenoPilot acts as an autonomous execution layer. Marketers specify a high-level revenue or engagement goal, and the AI agent loop automatically generates target audience segments, drafts optimized messaging, predicts delivery and conversion metrics, runs safety/spam analysis, dispatches messages, and reviews conversion performance.

## Key Features

1. **AI Agent Goal Mode**: markters specify high-level goals like "Win back VIP customers who haven't ordered in 60 days". The AI agent loop parses the query, defines database filters, drafts channel messages, calculates spam/readiness scores, and runs simulated dispatch.
2. **Proactive Opportunities Hub**: Background scanner that audits customer intelligence records periodically (e.g. churn risk, purchase frequency, engagement drops) and surfaces one-click executable campaigns.
3. **Natural Language Segmentation**: Translate natural language segments into structured JSON AST queries that compile down to optimized raw SQL database commands.
4. **Heuristic KPI Dashboard**: Attributed Revenue tracking, Funnel conversion analytics (Sent -> Delivered -> Opened -> Clicked -> Converted), channel performance comparison, and churn win-back rates.
5. **Customer Intelligence Profiles**: Recalculates churn likelihood, predicted lifetime value (LTV), affinity categories, preferred channel, and next best action recommendation per customer.
6. **Channel Simulator & Callback Webhooks**: Celery worker simulates messaging delivery status changes (sent, delivered, opened, clicked, converted) and reports them back to the core service through secure webhook receipts.

---

## Tech Stack

* **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS, Lucide icons, Recharts.
* **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Celery.
* **AI Layer**: OpenAI GPT-4o-mini integration, structured JSON AST generation.

---

## Setup & Running

### Option 1: Docker Compose (Recommended)

To run the entire stack (Postgres, Redis, Backend API, Celery Worker, and Next.js Frontend) in one command:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your `OPENAI_API_KEY`.
3. Launch all containers:
   ```bash
   docker compose up --build
   ```
4. Access the apps:
   * **Frontend**: http://localhost:3000
   * **FastAPI Docs**: http://localhost:8000/docs

### Option 2: Local Manual Setup

If you prefer to run services manually on your local machine:

#### Prerequisites
* Node.js v18+ & npm
* Python 3.11+
* PostgreSQL running locally
* Redis running locally

#### 1. Backend Setup
1. Navigate to backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment file and configure it:
   ```bash
   cp .env.example .env
   # Modify DB credentials and add your OPENAI_API_KEY
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### 2. Celery Worker Setup
1. In a new terminal window, activate the virtual environment inside `backend`:
   ```bash
   cd backend
   source venv/bin/activate
   ```
2. Launch the worker:
   ```bash
   celery -A celery_worker worker --loglevel=info
   ```

#### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install --legacy-peer-deps
   ```
3. Start the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:3000 in your browser.

---

## Sandbox Administration

When launching XenoPilot for the first time, navigate to the Dashboard and click the **"Seed Mock Data"** button at the top right. This will:
1. Populate your database with mock customers and realistic multi-category purchase histories.
2. Calculate and bootstrap their Customer Intelligence profiles.
3. Audit and surface proactive growth opportunities in the Opportunities Feed.
