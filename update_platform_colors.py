import asyncio
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from app.db.models import PlatformOption, Base # Assuming PlatformOption is in app/db/models
from app.config import settings # Assuming you have a settings module for database URL

# Define your database URL (e.g., from settings or directly)
DATABASE_URL = settings.database_url # or "postgresql+asyncpg://user:password@host/dbname"

# Example colors - MODIFY THESE AS NEEDED
PLATFORM_COLORS = {
    1281: "#0070D1",  # PlayStation 5 (Blue)
    1280: "#003791",  # PlayStation 4 (Darker Blue)
    1279: "#6B6B6B",  # PlayStation 3 (Gray)
    1278: "#A0A0A0",  # PlayStation 2 (Lighter Gray)
    1277: "#C0C0C0",  # PlayStation 1 (Even Lighter Gray)
    1286: "#E60012",  # PlayStation Portable (Red)
    1287: "#663399",  # PlayStation Vita (Purple)
    1282: "#107C10",  # Xbox Series X/S (Green)
    1283: "#1F7A1F",  # Xbox One (Darker Green)
    1284: "#339933",  # Xbox 360 (Medium Green)
    1285: "#4CAF50",  # Xbox (Lighter Green)
    1288: "#E4000F",  # Nintendo Switch (Red)
    1289: "#009ACD",  # Nintendo Wii U (Light Blue)
    1290: "#808080",  # Nintendo Wii (Gray)
    1291: "#FFD700",  # Nintendo DS (Gold)
    1292: "#FF69B4",  # Nintendo 3DS (Hot Pink)
    1293: "#607D8B",  # Nintendo GameCube (Blue-Gray)
    1294: "#9C27B0",  # Nintendo 64 (Purple)
    1295: "#000000",  # Game Boy (Black)
    1296: "#008CBA",  # Sega (Teal)
    1297: "#FF5722",  # PC Gaming (Orange)
}

async def update_platform_colors():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    async with async_session() as session:
        async with session.begin():
            for platform_id, color_code in PLATFORM_COLORS.items():
                stmt = select(PlatformOption).where(PlatformOption.id == platform_id)
                result = await session.execute(stmt)
                platform = result.scalar_one_or_none()

                if platform:
                    platform.color = color_code
                    print(f"Updated Platform ID {platform_id} ({platform.name}) with color {color_code}")
                else:
                    print(f"Platform with ID {platform_id} not found.")
            await session.commit()

if __name__ == "__main__":
    # This part assumes you have an event loop running or can run one.
    # For a simple script, you can run it directly:
    asyncio.run(update_platform_colors())
