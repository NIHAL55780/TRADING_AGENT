import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from agents.fundamental_agent import run_fundamental_agent
from agents.news_agent import run_news_agent
from agents.sentiment_agent import run_sentiment_agent
from agents.technical_agent import run_technical_agent

__all__ = [
    "run_fundamental_agent",
    "run_technical_agent",
    "run_news_agent",
    "run_sentiment_agent",
]
