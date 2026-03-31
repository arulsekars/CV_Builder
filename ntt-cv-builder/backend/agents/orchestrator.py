"""
agents/orchestrator.py
Central orchestrator that:
 1. Runs the Triage Agent via the OpenAI Agents SDK
 2. Interprets tool call results and mutates CVData
 3. Triggers RAG enrichment at the right moment
 4. Manages stage transitions
 5. Yields streaming tokens back to the WebSocket
"""
from __future__ import annotations
import json
import uuid
from typing import AsyncIterator, Optional

from agents import Runner, RunConfig
from agents.triage_agent import create_triage_agent
from agents.validation_agent import validate_cv_completeness, enrich_bullet_points
from rag.retriever import get_rag_context
from schemas.cv_schema import (
    CVData, SessionState, ContactInfo, WorkExperience,
    Education, Skill, Certification
)
from config import get_settings

settings = get_settings()


def apply_tool_result(cv: CVData, tool_result: str) -> tuple[CVData, Optional[str]]:
    """
    Parse a tool call result JSON and apply it to the CVData object.
    Returns (updated_cv, optional_signal) where signal can be 'generate_cv' etc.
    """
    try:
        result = json.loads(tool_result)
    except (json.JSONDecodeError, TypeError):
        return cv, None

    action = result.get("action")

    if action == "update_contact":
        fields = result.get("fields", {})
        current = cv.contact.model_dump()
        current.update({k: v for k, v in fields.items() if v is not None})
        cv.contact = ContactInfo(**current)

    elif action == "add_work_experience":
        entry = result.get("entry", {})
        cv.work_experience.append(WorkExperience(**entry))

    elif action == "add_education":
        entry = result.get("entry", {})
        cv.education.append(Education(**entry))

    elif action == "set_skills":
        skills_data = result.get("skills", [])
        cv.skills = [Skill(**s) for s in skills_data]

    elif action == "set_summary":
        cv.professional_summary = result.get("summary")

    elif action == "set_target_role":
        cv.target_role = result.get("role")
        cv.target_industry = result.get("industry")

    elif action == "select_template":
        cv.selected_template = result.get("template", "professional")

    elif action == "generate_cv":
        return cv, "generate_cv"

    elif action == "get_completion_status":
        return cv, "get_completion_status"

    return cv, None


class CVOrchestrator:
    """
    Manages a single user session: holds state, runs the agent, applies tool results.
    One instance per WebSocket session.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.cv = CVData()
        self.conversation_history: list[dict] = []
        self.stage = "greeting"
        self.agent = create_triage_agent()

    async def process_message(self, user_message: str) -> AsyncIterator[dict]:
        """
        Process a user message through the agent pipeline.
        Yields structured events: {"type": "token"|"tool"|"stage"|"cv_update"|"generate", "data": ...}
        """
        self.conversation_history.append({"role": "user", "content": user_message})

        # Build messages for the agent (include system context about current CV state)
        context_note = self._build_context_note()
        messages = [
            {"role": "system", "content": context_note},
            *self.conversation_history,
        ]

        try:
            result = await Runner.run(
                self.agent,
                input=messages,
                run_config=RunConfig(
                    model=settings.llm_model,
                    model_settings={"temperature": 0.7},
                    max_turns=8,
                ),
            )

            # Process tool calls that happened during the run
            for item in result.new_items:
                # Handle tool call outputs
                if hasattr(item, "output"):
                    cv, signal = apply_tool_result(self.cv, item.output)
                    self.cv = cv
                    yield {"type": "cv_update", "data": self.cv.model_dump()}

                    if signal == "generate_cv":
                        yield {"type": "stage", "data": "generating"}
                        self.stage = "generating"
                        async for gen_event in self._run_generation_pipeline():
                            yield gen_event
                        return

                    elif signal == "get_completion_status":
                        status = validate_cv_completeness(self.cv)
                        yield {"type": "validation", "data": status}

            # Get the final text response
            final_text = result.final_output if result.final_output else ""
            if final_text:
                self.conversation_history.append(
                    {"role": "assistant", "content": final_text}
                )
                yield {"type": "message", "data": final_text}

        except Exception as e:
            yield {
                "type": "error",
                "data": f"I encountered an issue processing your message. Please try again. ({str(e)})",
            }

    async def process_uploaded_cv(self, cv_data: CVData) -> AsyncIterator[dict]:
        """
        Handle the result of a parsed uploaded document.
        Merges with existing CV state and continues the conversation.
        """
        from agents.extraction_agent import merge_extracted_cv
        self.cv = await merge_extracted_cv(self.cv, cv_data)
        yield {"type": "cv_update", "data": self.cv.model_dump()}

        # Generate a contextual message summarising what was found
        summary_msg = await self._summarise_parsed_cv()
        self.conversation_history.append({"role": "assistant", "content": summary_msg})
        yield {"type": "message", "data": summary_msg}

    async def _run_generation_pipeline(self) -> AsyncIterator[dict]:
        """
        Run the full generation pipeline:
        1. RAG enrichment of bullet points
        2. Generate HTML preview
        3. Generate PDF + DOCX
        Yields progress events.
        """
        yield {"type": "progress", "data": "Enriching your CV with best-practice content..."}

        # RAG enrichment
        role_context = f"{self.cv.target_role or 'professional'} in {self.cv.target_industry or 'industry'}"
        rag_context = await get_rag_context(role_context)
        self.cv = await enrich_bullet_points(self.cv, rag_context)
        yield {"type": "cv_update", "data": self.cv.model_dump()}

        yield {"type": "progress", "data": "Rendering your CV..."}

        # Generate HTML preview
        from renderers.pdf_renderer import render_html_preview
        html_preview = render_html_preview(self.cv)
        yield {"type": "preview", "data": html_preview}

        # Generate downloadable files
        from renderers.pdf_renderer import render_pdf
        from renderers.docx_renderer import render_docx
        import base64

        pdf_bytes = render_pdf(self.cv)
        docx_bytes = render_docx(self.cv)

        yield {
            "type": "downloads_ready",
            "data": {
                "pdf_b64": base64.b64encode(pdf_bytes).decode(),
                "docx_b64": base64.b64encode(docx_bytes).decode(),
                "json": self.cv.model_dump(),
                "filename_stem": (self.cv.contact.full_name or "cv").replace(" ", "_").lower(),
            },
        }

        yield {
            "type": "message",
            "data": f"✅ Your CV is ready! You can download your PDF, Word document, or JSON below.\n\nIf you'd like any changes, just let me know!",
        }
        self.stage = "done"

    def _build_context_note(self) -> str:
        """Build a system context note showing current CV state to the agent."""
        missing = self.cv.missing_required_fields()
        completion = self.cv.completion_percentage()
        name = self.cv.contact.full_name or "the user"
        return f"""
Current session context:
- User: {name}
- CV completion: {completion}%
- Missing required fields: {', '.join(missing) if missing else 'None — CV is complete!'}
- Current stage: {self.stage}
- Work experience entries: {len(self.cv.work_experience)}
- Education entries: {len(self.cv.education)}
- Skills listed: {len(self.cv.skills)}

Use this context to avoid asking for information already collected.
If completion is 100%, move to the template selection stage.
""".strip()

    async def _summarise_parsed_cv(self) -> str:
        """Generate a friendly summary of what was found in the uploaded CV."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        cv_dict = self.cv.model_dump()
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a friendly CV assistant. Summarise what was found in an uploaded CV in 2-3 sentences, then ask what the user would like to update or confirm. Be warm and specific.",
                },
                {
                    "role": "user",
                    "content": f"Uploaded CV data: {json.dumps(cv_dict, indent=2)}",
                },
            ],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
