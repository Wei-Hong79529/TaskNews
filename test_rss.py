from dotenv import load_dotenv
load_dotenv()
from app.utils import setup_logging, format_news_report
setup_logging()
from app.main import run_daily_job
run_daily_job()
