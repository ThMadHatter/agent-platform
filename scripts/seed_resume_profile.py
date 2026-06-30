import asyncio
import sys
import os
import yaml
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.getcwd())

from core.config import settings
from database.models import ResumeProfile

async def seed_profile(yaml_path: str):
    if not os.path.exists(yaml_path):
        print(f"Error: Profile YAML not found at {yaml_path}")
        return

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    profile_id = data.get("profile_id", "matteo-default")

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
            profile.name = data.get("name", profile.name)
            profile.contacts = data.get("contacts", profile.contacts)
            profile.languages = data.get("languages", profile.languages)
            profile.summary = data.get("summary", profile.summary)
        else:
            print(f"Creating profile {profile_id}...")
            profile = ResumeProfile(
                id=profile_id,
                name=data.get("name"),
                contacts=data.get("contacts", []),
                languages=data.get("languages", []),
                summary=data.get("summary")
            )
            session.add(profile)

        await session.commit()
        print(f"Successfully seeded profile: {profile_id}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed resume profile from YAML")
    parser.add_argument("--file", default="config/resume_profile.yaml", help="Path to profile YAML")
    args = parser.parse_args()

    asyncio.run(seed_profile(args.file))
