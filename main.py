from backend.gmail.fetch import fetch_tnp_emails
from backend.graph.graph import workflow
from backend.db.database import create_db_and_tables, get_session
from backend.db.crud import get_or_create_user, is_duplicate_email, save_email, save_extraction_result
from backend.pipeline import run_pipeline

if __name__ == "__main__":
     run_pipeline()
   