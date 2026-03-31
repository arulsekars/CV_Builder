"""
Validation Agent
────────────────
Checks the CV schema for completeness and generates targeted
follow-up questions for any gaps. One gap = one question.
"""
import logging
from typing import List, Optional, Tuple
from openai import AsyncOpenAI
from backend.core.schema import CVData

logger = logging.getLogger(__name__)

VALIDATION_PROMPT = """You are a CV validation assistant. 
Given a partially completed CV and a list of missing fields,
generate ONE friendly, specific follow-up question to collect the most important missing information.

Missing fields: {missing}
CV so far: {cv_summary}

Rules:
- Ask about the SINGLE most important missing field
- Be conversational and encouraging
- Give an example if helpful (e.g., "e.g., Led a team of 5 engineers...")
- Keep it to 1-2 sentences

Respond with just the question, no preamble.
"""


async def validate_and_prompt(
    cv_data: CVData,
    client: AsyncOpenAI,
    model: str = "gpt-4o",
) -> Tuple[bool, Optional[str]]:
    """
    Check CV completeness.
    Returns (is_complete, follow_up_question_or_None).
    """
    missing = cv_data.missing_required_fields()

    if not missing:
        # Also check quality of work experience bullets
        quality_issues = _check_quality(cv_data)
        if quality_issues:
            missing = quality_issues

    if not missing:
        return True, None

    # Generate targeted question for the top missing item
    cv_summary = _summarise_cv(cv_data)

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{
                "role": "user",
                "content": VALIDATION_PROMPT.format(
                    missing=", ".join(missing[:3]),
                    cv_summary=cv_summary,
                )
            }],
            temperature=0.6,
            max_tokens=150,
        )
        question = response.choices[0].message.content.strip()
        return False, question

    except Exception as e:
        logger.error(f"Validation agent error: {e}")
        # Fallback question
        return False, f"Could you tell me more about your {missing[0]}?"


def _check_quality(cv_data: CVData) -> List[str]:
    """Check for quality issues beyond required field presence."""
    issues = []
    for exp in cv_data.work_experience:
        if not exp.bullets:
            issues.append(f"achievements/bullet points for your role at {exp.company or 'your previous employer'}")
            break
        if len(exp.bullets) < 2:
            issues.append(f"more detail about your achievements at {exp.company or 'your previous employer'}")
            break
    return issues


def _summarise_cv(cv_data: CVData) -> str:
    lines = []
    if cv_data.full_name:
        lines.append(f"Name: {cv_data.full_name}")
    if cv_data.headline:
        lines.append(f"Role: {cv_data.headline}")
    if cv_data.work_experience:
        lines.append(f"Experience entries: {len(cv_data.work_experience)}")
        for w in cv_data.work_experience[:2]:
            lines.append(f"  - {w.job_title} at {w.company} ({len(w.bullets)} bullets)")
    if cv_data.education:
        lines.append(f"Education: {cv_data.education[0].degree} at {cv_data.education[0].institution}")
    if cv_data.skills:
        lines.append(f"Skills: {', '.join(cv_data.skills[:8])}")
    return "\n".join(lines)
