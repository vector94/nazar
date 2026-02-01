# Nazar

**Every production system fails sometimes, no matter how carefully it's built. The difference is whether you catch it before your users do.**

Nazar is a performance monitoring platform that collects server metrics, detects anomalies using statistical and ML approaches, and alerts you before small issues become outages. Cloud infrastructure, on-premise servers, or containerized applications: if it generates metrics, Nazar can monitor it.

## Features

- Metric collection via agents or REST API
- Time-series storage with TimescaleDB
- Anomaly detection (statistical + ML)
- Multi-channel alerts (Slack, Email)
- Web dashboard for visualization

## Tech Stack

- **Backend**: Python, FastAPI
- **Database**: TimescaleDB
- **Message Broker**: RabbitMQ
- **Frontend**: React
- **Deployment**: Docker

## Project Structure

```
nazar/
├── backend/
│   ├── api/        # FastAPI server
│   ├── worker/     # Analysis worker
│   └── shared/     # Shared code
├── frontend/       # React dashboard
├── docker/         # Docker configs
└── docs/           # Architecture docs (arc42)
```

## Getting Started

```bash
# Start infrastructure
docker-compose up -d

# Run API server
cd backend/api && uvicorn main:app --reload

# Run worker
cd backend/worker && python main.py
```

## Documentation

Architecture documentation available in `docs/arc42/nazar-architecture.pdf`
