"""
tools/cv_tools.py
Function tools registered with the OpenAI Agents SDK.
Each function is decorated with @function_tool and made available to agents.
"""
from __future__ import annotations
import json
from typing import Optional
from agents import function_tool
from schemas.cv_schema import CVData, WorkExperience, Education, Skill, Certification


@function_tool
def update_contact_info(
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
) -> str:
    """
    Update the candidate's contact information fields.
    Only pass the fields that have been confirmed by the user.
    Returns a JSON string of the updated fields.
    """
    fields = {k: v for k, v in locals().items() if v is not None}
    return json.dumps({"action": "update_contact", "fields": fields})


@function_tool
def add_work_experience(
    job_title: str,
    company: str,
    start_date: str,
    end_date: Optional[str],
    is_current: bool,
    description: str,
    technologies: Optional[list[str]] = None,
) -> str:
    """
    Add a work experience entry to the CV.
    Call this once per role the user describes.
    end_date should be None if is_current is True.
    """
    entry = {
        "job_title": job_title,
        "company": company,
        "start_date": start_date,
        "end_date": end_date,
        "is_current": is_current,
        "description": description,
        "technologies": technologies or [],
    }
    return json.dumps({"action": "add_work_experience", "entry": entry})


@function_tool
def add_education(
    degree: str,
    institution: str,
    start_date: Optional[str],
    end_date: Optional[str],
    grade: Optional[str] = None,
) -> str:
    """
    Add an education entry to the CV.
    Call this once per qualification the user describes.
    """
    entry = {
        "degree": degree,
        "institution": institution,
        "start_date": start_date,
        "end_date": end_date,
        "grade": grade,
    }
    return json.dumps({"action": "add_education", "entry": entry})


@function_tool
def set_skills(skills: list[dict]) -> str:
    """
    Set the skills list. Each item should have 'name' and optionally 'level' and 'category'.
    Example: [{"name": "Python", "level": "expert", "category": "Programming"}]
    """
    return json.dumps({"action": "set_skills", "skills": skills})


@function_tool
def set_professional_summary(summary: str) -> str:
    """
    Set the professional summary paragraph for the CV.
    This should be a concise, impactful 2-4 sentence summary of the candidate.
    """
    return json.dumps({"action": "set_summary", "summary": summary})


@function_tool
def set_target_role(role: str, industry: Optional[str] = None) -> str:
    """
    Record the candidate's target job role and optionally their target industry.
    This helps the RAG system retrieve the most relevant best-practice bullets.
    """
    return json.dumps({"action": "set_target_role", "role": role, "industry": industry})


@function_tool
def get_cv_completion_status() -> str:
    """
    Check what fields are still missing from the CV.
    Returns a JSON object with missing fields and completion percentage.
    Use this before moving to the validation stage.
    """
    # Signal to the orchestrator to compute this from live CV state
    return json.dumps({"action": "get_completion_status"})


@function_tool
def select_template(template_key: str) -> str:
    """
    Record the user's chosen CV template.
    Available templates: 'professional', 'modern', 'minimal', 'executive'.
    """
    valid = ["professional", "modern", "minimal", "executive"]
    if template_key not in valid:
        return json.dumps({"error": f"Unknown template. Choose from: {valid}"})
    return json.dumps({"action": "select_template", "template": template_key})


@function_tool
def trigger_cv_generation() -> str:
    """
    Signal that the user has approved the CV and it should be generated.
    Call this only after the user explicitly confirms they are happy with the preview.
    """
    return json.dumps({"action": "generate_cv"})
