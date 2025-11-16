"""Initialize database with all tables."""

import asyncio
from core.database import engine, Base
from core.models import User, Agent, KnowledgeBase, Document, ChatSession, ChatMessage


async def init_database():
    """Create all database tables."""
    print("Creating database tables...")

    async with engine.begin() as conn:
        # Drop all tables (be careful in production!)
        await conn.run_sync(Base.metadata.drop_all)
        print("  Dropped existing tables")

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("  Created all tables")

    print("✅ Database initialization complete!")

    # Print table names
    print("\nCreated tables:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")


if __name__ == "__main__":
    asyncio.run(init_database())
