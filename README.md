# Nazar

A performance monitoring platform: agents collect system metrics, a worker flags
anomalies with threshold rules and an Isolation Forest model, and alerts go to
Slack. A React dashboard streams the data live.

![Nazar dashboard](assets/dashboard.png)

## Architecture

```mermaid
flowchart LR
    Agent["Agent<br/>(psutil)"] -->|POST /metrics| API["API<br/>(FastAPI)"]
    API -->|store| DB[("TimescaleDB")]
    API -->|publish| MQ[["RabbitMQ"]]
    MQ -->|consume| Worker["Worker<br/>(threshold + ML)"]
    Worker <-->|metrics / alerts| DB
    Worker -->|notify| Slack["Slack"]
    API -->|SSE| Dashboard["Dashboard<br/>(React)"]
```

Agents sample once per second and POST a 10-second min/max/avg aggregate. The API
stores each metric in TimescaleDB and publishes a notification to RabbitMQ. The
worker reads the metric back, runs threshold checks and Isolation Forest
detection, writes any alerts, and posts them to Slack. The dashboard consumes a
live SSE feed from the API.

Threshold alerts are tracked per host and metric, with at most one open
(`pending` or `acknowledged`) at a time. Crossing a threshold raises one; rising
from warning to critical replaces it with a critical alert; dropping back below
the warning level marks it `resolved`. Acknowledging an alert
(`PATCH /alerts/{id}`) keeps it open without raising it again.

## Stack

| Layer    | Technology                      |
| -------- | ------------------------------- |
| API      | Python, FastAPI                 |
| Database | TimescaleDB (PostgreSQL)        |
| Queue    | RabbitMQ                        |
| ML       | scikit-learn (Isolation Forest) |
| Frontend | React, TypeScript, Vite         |
| Agent    | Python, psutil                  |

## Layout

```
agent/       psutil collector + aggregation/send loop
backend/
  api/       FastAPI REST + SSE endpoints
  worker/    RabbitMQ consumer: threshold + ML detection, Slack alerts
  shared/    SQLAlchemy models, DB session, RabbitMQ client
  tests/     pytest suite
frontend/    React dashboard (Vite)
docker/      Compose file for TimescaleDB + RabbitMQ
docs/arc42/  Architecture documentation
```

## Running locally

Requires Docker, Python 3.9+, and Node.js 18+.

```bash
# infrastructure
cd docker && docker compose up -d

# backend
cd backend
cp .env.example .env          # set SLACK_WEBHOOK_URL for alerts
pip install -r requirements.txt
python -m shared.init_db      # first run only
python -m uvicorn api.main:app --port 8000 &
python -m worker.main &

# agent
cd ../agent
pip install -r requirements.txt
python main.py &

# dashboard
cd ../frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173 · API docs: http://localhost:8000/docs

## Tests

The backend tests run against a temporary SQLite database, so they don't need
Docker.

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```

## Configuration

| Variable            | Description                                          | Default                                                   |
| ------------------- | --------------------------------------------------- | --------------------------------------------------------- |
| `DATABASE_URL`      | PostgreSQL connection string                        | `postgresql+asyncpg://nazar:nazar123@localhost:5433/nazar` |
| `RABBITMQ_URL`      | RabbitMQ connection string                          | `amqp://nazar:nazar123@localhost:5672/`                    |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook; alerts are log-only if unset | –                                                        |
| `NAZAR_API_URL`     | API URL the agent posts to                          | `http://localhost:8000`                                    |
| `NAZAR_HOSTNAME`    | Host label reported by the agent                    | system hostname                                            |
| `NAZAR_INTERVAL`    | Agent send interval, seconds                        | `10`                                                      |

## Documentation

Architecture decisions, C4 diagrams, and runtime scenarios: [docs/arc42/nazar-architecture.pdf](docs/arc42/nazar-architecture.pdf).
