import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.db.models import SourceOption, Base # Assuming SourceOption is in app/db/models
from app.config import settings # Assuming you have a settings module for database URL

# Define your database URL (e.g., from settings or directly)
DATABASE_URL = settings.database_url # or "postgresql+asyncpg://user:password@host/dbname"

# Sources to ensure exist in the database
# Add any other sources you expect to have here
REQUIRED_SOURCES = [
    {"code": "vinted", "label": "Vinted", "color": "#00B289"}, # Example color for Vinted
    # {"code": "ebay", "label": "eBay", "color": "#E53238"},
    # {"code": "facebook", "label": "Facebook Marketplace", "color": "#1877F2"},
]

async def ensure_sources_exist():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        async with session.begin():
            for source_data in REQUIRED_SOURCES:
                stmt = select(SourceOption).where(SourceOption.code == source_data["code"])
                result = await session.execute(stmt)
                source_option = result.scalar_one_or_none()

                if source_option:
                    # Update existing source if needed (e.g., color)
                    if source_option.label != source_data["label"]:
                        source_option.label = source_data["label"]
                    if source_option.color != source_data["color"]:
                        source_option.color = source_data["color"]
                    print(f"Source '{source_data['code']}' already exists. Updated if necessary.")
                else:
                    new_source = SourceOption(
                        code=source_data["code"],
                        label=source_data["label"],
                        color=source_data["color"]
                    )
                    session.add(new_source)
                    print(f"Added new source: '{source_data['code']}'")
            await session.commit()

if __name__ == "__main__":
    asyncio.run(ensure_sources_exist())
