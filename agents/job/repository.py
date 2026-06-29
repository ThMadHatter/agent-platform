from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from database.models import Job, JobMatch, CVGenerationRun, CVKnowledgeItem, ResumeProfile, Artifact

class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_job(self, job_data: Dict[str, Any]) -> Job:
        job = Job(**job_data)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        stmt = select(Job).where(Job.id == job_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_job_by_url(self, url: str) -> Optional[Job]:
        stmt = select(Job).where(Job.source_url == url)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_match_result(self, match_data: Dict[str, Any]) -> JobMatch:
        match = JobMatch(**match_data)
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def save_cv_generation_run(self, run_data: Dict[str, Any]) -> CVGenerationRun:
        run = CVGenerationRun(**run_data)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def update_cv_generation_run(self, run_id: str, update_data: Dict[str, Any]) -> None:
        stmt = update(CVGenerationRun).where(CVGenerationRun.id == run_id).values(**update_data)
        await self.session.execute(stmt)
        await self.session.commit()

    async def save_artifact_reference(self, artifact_data: Dict[str, Any]) -> Artifact:
        artifact = Artifact(**artifact_data)
        self.session.add(artifact)
        await self.session.commit()
        await self.session.refresh(artifact)
        return artifact

    async def get_resume_profile(self, profile_id: str) -> Optional[ResumeProfile]:
        stmt = select(ResumeProfile).where(ResumeProfile.id == profile_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_resume_profile(self, profile_data: Dict[str, Any]) -> ResumeProfile:
        profile = ResumeProfile(**profile_data)
        self.session.add(profile)
        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def save_cv_knowledge_item(self, item_data: Dict[str, Any]) -> CVKnowledgeItem:
        item = CVKnowledgeItem(**item_data)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def list_cv_knowledge_items(self, profile_id: str) -> List[CVKnowledgeItem]:
        stmt = select(CVKnowledgeItem).where(CVKnowledgeItem.resume_profile_id == profile_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
