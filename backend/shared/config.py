import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://nazar:nazar123@localhost:5433/nazar")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://nazar:nazar123@localhost:5672/")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
