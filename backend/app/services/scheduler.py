from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import SessionLocal
from app.services.schwab_auth import SchwabAuthService

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    async def check_token_expiry(self):
        """Checks if the token is about to expire and refreshes it if needed."""
        print("Running scheduled task: check_token_expiry")
        db = SessionLocal()
        try:
            await SchwabAuthService.get_active_token(db)
        except Exception as e:
            print(f"Error in check_token_expiry: {e}")
        finally:
            db.close()

    def start(self):
        """Starts the scheduler."""
        # Check every 15 minutes
        self.scheduler.add_job(self.check_token_expiry, 'interval', minutes=15)
        self.scheduler.start()
        print("Scheduler started.")
