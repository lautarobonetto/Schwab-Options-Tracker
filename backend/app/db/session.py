from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# SQLite specific check
connect_args = {"check_same_thread": False}

engine = create_engine(
    f"sqlite:///{settings.SQLITE_DB_PATH}",
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
