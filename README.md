# Nazar

A performance monitoring platform that collects system metrics, detects anomalies using statistical thresholds and machine learning, and sends alerts before issues escalate.

![Nazar dashboard streaming live host metrics](assets/dashboard.png)

## How It Works

```mermaid
flowchart LR
    Agent["Agent<br/>(psutil collector)"] -->|POST /metrics| API["API Server<br/>(FastAPI)"]
    API -->|store| DB[("TimescaleDB")]
    API -->|publish| MQ[["RabbitMQ"]]
    MQ -->|consume| Worker["Worker<br/>(threshold + ML<br/>anomaly detection)"]
    Worker <-->|read metrics /<br/>write alerts| DB
    Worker -->|notify| Slack["Slack"]
    API -->|SSE stream| Dashboard["Dashboard<br/>(React)"]
```

1. **Agents** sample system metrics every 1 second and send aggregated data (min/max/avg) every 10 seconds
2. **API Server** stores metrics in TimescaleDB and publishes to RabbitMQ
3. **Worker** consumes messages and runs anomaly detection:
   - Threshold-based: alerts when metrics exceed configured limits
   - ML-based: Isolation Forest detects unusual patterns in metric combinations
4. **Alerts** are sent to Slack when anomalies are detected
5. **Dashboard** displays real-time metrics via Server-Sent Events (SSE)

## Tech Stack

| Layer         | Technology                      |
| ------------- | ------------------------------- |
| API           | Python, FastAPI                 |
| Database      | TimescaleDB (PostgreSQL)        |
| Message Queue | RabbitMQ                        |
| ML            | scikit-learn (Isolation Forest) |
| Frontend      | React, TypeScript, Vite         |
| Agent         | Python, psutil                  |

## Project Structure

```
nazar/
├── agent/                 # System metric collector (psutil)
│   ├── collector.py       #   samples CPU, memory, disk, network
│   └── main.py            #   aggregation + send loop
├── backend/
│   ├── api/               # FastAPI REST + SSE endpoints
│   ├── worker/            # RabbitMQ consumer
│   │   ├── detector.py    #   threshold-based detection
│   │   ├── ml_detector.py #   Isolation Forest detection
│   │   └── notifier.py    #   Slack alerts
│   └── shared/            # SQLAlchemy models, DB session, RabbitMQ client
├── frontend/              # React dashboard (Vite + TypeScript)
├── docker/                # Docker Compose (TimescaleDB, RabbitMQ)
├── assets/                # README screenshots
└── docs/arc42/            # Architecture documentation
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

<details>
<summary>📷 API documentation (Swagger UI)</summary>

![Interactive API documentation](assets/api-docs.png)

</details>

## Configuration

| Variable              | Description                         | Default                                                   |
| --------------------- | ----------------------------------- | --------------------------------------------------------- |
| `DATABASE_URL`      | PostgreSQL connection string        | `postgresql+asyncpg://nazar:nazar@localhost:5432/nazar` |
| `RABBITMQ_URL`      | RabbitMQ connection string          | `amqp://guest:guest@localhost:5672/`                    |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL          | -                                                         |
| `NAZAR_API_URL`     | API URL for agent                   | `http://localhost:8000`                                 |
| `NAZAR_INTERVAL`    | Agent collection interval (seconds) | `10`                                                    |

## Documentation

For detailed architecture decisions, component diagrams, and runtime scenarios, see the arc42 documentation:

**[📄 Architecture Document (PDF)](docs/arc42/nazar-architecture.pdf)**

The documentation covers:

- System context and building blocks
- Architectural decisions (ADRs)
- Runtime scenarios
- Quality requirements
