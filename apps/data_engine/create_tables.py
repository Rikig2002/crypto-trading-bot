from apps.data_engine.database import Base, engine
from apps.data_engine.models import MarketData, StrategySignal, Trade


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_tables()
