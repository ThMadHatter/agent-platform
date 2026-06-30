from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class TypstPersonalContact(BaseModel):
    icon: str
    icon_solid: bool = True
    text: str
    link: str = ""

class TypstPersonal(BaseModel):
    name: str
    title: str
    contacts: List[TypstPersonalContact] = []

class TypstSkillGroup(BaseModel):
    name: str
    icon: str = "tools"
    skills: List[str]

class TypstLanguage(BaseModel):
    flag: str
    name: str
    level: float # 0 to 1

class TypstPoint(BaseModel):
    icon: str = "check"
    icon_solid: bool = False
    text: str

class TypstExperience(BaseModel):
    company: str
    title: str
    date: str
    description: str = ""
    points: List[TypstPoint] = []

class TypstAchievement(BaseModel):
    title: str
    items: List[TypstPoint] = []

class TypstEducation(BaseModel):
    institution: str
    date: str
    location: str = ""
    icon: str = "graduation-cap"
    degree: str
    gpa: str = ""
    points: List[TypstPoint] = []

class TypstLayout(BaseModel):
    sidebar_position: str = "left"

class TypstCVData(BaseModel):
    layout: TypstLayout = Field(default_factory=TypstLayout)
    personal: TypstPersonal
    about_me: str = ""
    skills: List[TypstSkillGroup] = []
    languages: List[TypstLanguage] = []
    experience: List[TypstExperience] = []
    achievements: List[TypstAchievement] = []
    education: List[TypstEducation] = []

class TypstCVDataBuilder:
    @staticmethod
    def sanitize(data: Dict[str, Any]) -> Dict[str, Any]:
        def clean(obj):
            if isinstance(obj, dict):
                return {k: clean(v) for k, v in obj.items() if v is not None}
            elif isinstance(obj, list):
                return [clean(x) for x in obj if x is not None]
            return obj

        sanitized = clean(data)
        validated = TypstCVData(**sanitized)
        return validated.model_dump()

    @staticmethod
    def build_safe_filename(name: str, company: str, title: str) -> str:
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())
        safe_company = re.sub(r'[^a-zA-Z0-9]', '_', company.lower())
        safe_title = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
        return f"cv_{safe_name}_{safe_company}_{safe_title}.pdf"
