import asyncio
import uuid
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

from core.config import settings
from database.models import ResumeProfile

async def seed_profile(profile_id: str):
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        # Check if profile exists
        from sqlalchemy import select
        stmt = select(ResumeProfile).where(ResumeProfile.id == profile_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

        if profile:
            print(f"Profile {profile_id} already exists. Updating...")
            profile.name = "Matteo Zappia"
            profile.contacts = [
                {"icon": "envelope", "icon_solid": True, "text": "matteo.zappia@gmail.com", "link": "mailto:matteo.zappia@gmail.com"},
                {"icon": "linkedin", "icon_solid": False, "text": "LinkedIn", "link": "https://linkedin.com/in/matteo-zappia-0b8161114"},
                {"icon": "phone", "icon_solid": True, "text": "+39 ...", "link": ""}
            ]
            profile.languages = [
                {"flag": "IT", "name": "Italian", "level": 1.0},
                {"flag": "GB", "name": "English", "level": 0.8},
                {"flag": "DE", "name": "German", "level": 0.3}
            ]
        else:
            print(f"Creating profile {profile_id}...")
            profile = ResumeProfile(
                id=profile_id,
                name="Matteo Zappia",
                contacts=[
                    {"icon": "envelope", "icon_solid": True, "text": "matteo.zappia@gmail.com", "link": "mailto:matteo.zappia@gmail.com"},
                    {"icon": "linkedin", "icon_solid": False, "text": "LinkedIn", "link": "https://linkedin.com/in/matteo-zappia-0b8161114"},
                    {"icon": "phone", "icon_solid": True, "text": "+39 ...", "link": ""}
                ],
                languages=[
                    {"flag": "IT", "name": "Italian", "level": 1.0},
                    {"flag": "GB", "name": "English", "level": 0.8},
                    {"flag": "DE", "name": "German", "level": 0.3}
                ]
            )
            session.add(profile)

        await session.commit()
        print(f"Successfully seeded profile: {profile_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed resume profile")
    parser.add_argument("--profile", default="matteo-default", help="Profile ID to seed")
    args = parser.parse_args()

    asyncio.run(seed_profile(args.profile))
