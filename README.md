# Nazar

A performance monitoring platform that collects system metrics, detects anomalies using statistical thresholds and machine learning, and sends alerts before issues escalate.

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Agents    │────▶│  API Server │────▶│  Dashboard  │
│  (metrics)  │     │  (FastAPI)  │     │   (React)   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │                    ▲
                    ┌─────▼─────┐              │
                    │ RabbitMQ  │         SSE Stream
                    └─────┬─────┘              │
                          │                    │
                    ┌─────▼─────┐     ┌────────┴────────┐
                    │  Worker   │────▶│   TimescaleDB   │
                    │ (Anomaly  │     │  (Time-series)  │
                    │ Detection)│     └─────────────────┘
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │   Slack   │
                    │  Alerts   │
                    └───────────┘
```

1. **Agents** collect CPU, memory, disk metrics and push to the API every 10 seconds
2. **API Server** stores metrics in TimescaleDB and publishes to RabbitMQ
3. **Worker** consumes messages and runs anomaly detection:
   - Threshold-based: alerts when metrics exceed configured limits
   - ML-based: Isolation Forest detects unusual patterns in metric combinations
4. **Alerts** are sent to Slack when anomalies are detected
5. **Dashboard** displays real-time metrics via Server-Sent Events (SSE)

## Tech Stack

| Layer | Technology |
|-------|------------|
| API | Python, FastAPI |
| Database | TimescaleDB (PostgreSQL) |
| Message Queue | RabbitMQ |
| ML | scikit-learn (Isolation Forest) |
| Frontend | React, TypeScript, Vite |
| Agent | Python, psutil |

## Project Structure

```
nazar/
├── backend/
│   ├── api/           # FastAPI REST + SSE endpoints
│   ├── worker/        # Anomaly detection (threshold + ML)
│   └── shared/        # Database models, RabbitMQ client
├── frontend/          # React dashboard
├── agent/             # System metric collector
├── docker/            # Docker Compose for infrastructure
└── docs/arc42/        # Architecture documentation
```

## Quick Start

**Prerequisites:** Docker, Python 3.9+, Node.js 18+

```bash
# 1. Start infrastructure (TimescaleDB + RabbitMQ)
cd docker && docker-compose up -d

# 2. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your Slack webhook URL

# 3. Install and run backend
cd backend
pip install -r requirements.txt
python -m uvicorn api.main:app --port 8000 &
python -m worker.main &

# 4. Install and run agent
cd agent
pip install -r requirements.txt
python main.py &

# 5. Install and run dashboard
cd frontend
npm install
npm run dev
```

**Access:**
- Dashboard: http://localhost:5173
- API Docs: http://localhost:8000/docs

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://nazar:nazar@localhost:5432/nazar` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@localhost:5672/` |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL | - |
| `NAZAR_API_URL` | API URL for agent | `http://localhost:8000` |
| `NAZAR_INTERVAL` | Agent collection interval (seconds) | `10` |

## Documentation

For detailed architecture decisions, component diagrams, and runtime scenarios, see the arc42 documentation:

**[📄 Architecture Document (PDF)](docs/arc42/nazar-architecture.pdf)**

The documentation covers:
- System context and building blocks
- Architectural decisions (ADRs)
- Runtime scenarios
- Quality requirements
