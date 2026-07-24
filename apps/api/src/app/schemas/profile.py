from pydantic import BaseModel, Field
from typing import List, Optional

class Project(BaseModel):
    description: str = Field(..., description="Description of the project, workflow, or architectural implementation.")

class CVProfile(BaseModel):
    years_of_experience: str = Field(..., description="Total years of professional experience extracted from the summary or calculated from dates.")
    seniority: str = Field(..., description="Inferred seniority level based on job titles, progression, and responsibilities.")
    technologies_known: List[str] = Field(..., description="List of all programming languages, frameworks, cloud providers, and databases known.")
    projects_made: List[Project] = Field(..., description="List of significant projects or achievements detailed in the CV.")


class ContactInfo(BaseModel):
    """Contact section of a LinkedIn profile export."""

    email: Optional[str] = Field(default=None, description="Primary contact email address.")
    phone: Optional[str] = Field(default=None, description="Contact phone number, if present.")
    linkedin_url: Optional[str] = Field(default=None, description="Public LinkedIn profile URL.")
    websites: List[str] = Field(default_factory=list, description="Additional websites or links listed in the contact section.")


class LanguageProficiency(BaseModel):
    """A spoken language and its declared proficiency."""

    language: str = Field(..., description="Language name (e.g., English).")
    proficiency: Optional[str] = Field(default=None, description="Declared proficiency (e.g., Native or Bilingual).")


class Experience(BaseModel):
    """A single position held at a company."""

    company: str = Field(..., description="Company or organization name.")
    title: Optional[str] = Field(default=None, description="Role or job title held at the company.")
    date_range: Optional[str] = Field(default=None, description="Raw date range as rendered (e.g., 'June 2025 - Present').")
    duration: Optional[str] = Field(default=None, description="Human-readable tenure duration (e.g., '1 year 2 months').")
    location: Optional[str] = Field(default=None, description="Work location for the position, if present.")
    highlights: List[str] = Field(default_factory=list, description="Bullet points describing responsibilities and achievements.")


class Education(BaseModel):
    """A single education entry."""

    institution: str = Field(..., description="School, university, or institution name.")
    degree: Optional[str] = Field(default=None, description="Degree earned (e.g., Bachelor of Engineering).")
    field_of_study: Optional[str] = Field(default=None, description="Field or major of study.")
    date_range: Optional[str] = Field(default=None, description="Raw date range as rendered (e.g., 'April 2022 - April 2027').")


class LinkedInProfile(BaseModel):
    """Structured representation of a LinkedIn 'Save to PDF' export.

    This is the shape a CV PDF becomes after the strip step: the information
    rendered inside the document, extracted into typed fields. ``CVProfile`` is
    a downstream reduction of this model.
    """

    name: Optional[str] = Field(default=None, description="Full name of the profile owner.")
    headline: Optional[str] = Field(default=None, description="Professional headline / title line under the name.")
    location: Optional[str] = Field(default=None, description="Geographic location (city, region, country).")
    contact: ContactInfo = Field(default_factory=ContactInfo, description="Contact details section.")
    summary: Optional[str] = Field(default=None, description="Free-text 'Summary' / About section.")
    top_skills: List[str] = Field(default_factory=list, description="Items listed under 'Top Skills'.")
    languages: List[LanguageProficiency] = Field(default_factory=list, description="Items listed under 'Languages'.")
    certifications: List[str] = Field(default_factory=list, description="Items listed under 'Certifications'.")
    experiences: List[Experience] = Field(default_factory=list, description="Positions listed under 'Experience'.")
    education: List[Education] = Field(default_factory=list, description="Entries listed under 'Education'.")