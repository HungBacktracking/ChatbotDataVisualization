from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator

from app.schema.award_schema import AwardResponse
from app.schema.base_schema import ModelBaseInfo
from app.schema.education_schema import EducationResponse
from app.schema.experience_schema import ExperienceResponse
from app.schema.project_schema import ProjectResponse
from app.schema.skill_schema import SkillResponse
from app.util.regex import PASSWORD_REGEX


class BaseUser(BaseModel):
    email: EmailStr
    name: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(ModelBaseInfo, BaseUser): ...

