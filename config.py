import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"
PROMPTS_DIR = PROJECT_ROOT / "ai" / "prompts"

# Ensure output directories exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

# Load .env
load_dotenv(PROJECT_ROOT / ".env")

# 1. AI Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "offline").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# 2. Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes")

# 3. Data Sources
FIREANT_BEARER_TOKEN = os.getenv("FIREANT_BEARER_TOKEN", "")
DEFAULT_WATCHLIST = [
    t.strip().upper()
    for t in os.getenv("DEFAULT_WATCHLIST", "HPG,FPT,VCB,MBB,TCB,MWG,VHM,VIC,VNM,MSN,SSI,VND,DGC,VHC,PVD,GAS,STB,ACB,KDH,REE").split(",")
    if t.strip()
]

# 4. Trading & Strategy Thresholds (Hybrid Growth & Smart Money)
MIN_ROE = 12.0                  # Tối thiểu 12% ROE
MIN_REVENUE_GROWTH = 10.0       # Tăng trưởng doanh thu quý gần nhất > 10%
MIN_PROFIT_GROWTH = 15.0        # Tăng trưởng lợi nhuận quý gần nhất > 15%
MIN_PIOTROSKI_SCORE = 5         # Thang điểm Piotroski F-score tối thiểu (5/9)
MAX_DEBT_TO_EQUITY = 2.5        # Nợ vay / Vốn chủ sở hữu tối đa

VOLUME_BREAKOUT_FACTOR = 1.3    # Khối lượng nổ vol >= 1.3 lần MA20
MAX_STOP_LOSS_PCT = 0.07        # Cắt lỗ nghiêm ngặt tối đa 7%
MIN_RISK_REWARD_RATIO = 2.0     # Tỷ lệ R:R tối thiểu 2:1
TARGET_PROFIT_1_PCT = 0.12      # Mục tiêu lợi nhuận 1 (12%)
TARGET_PROFIT_2_PCT = 0.20      # Mục tiêu lợi nhuận 2 (20%)
