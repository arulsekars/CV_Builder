"""
LangChain RAG Retriever
────────────────────────
Uses LangChain + ChromaDB to retrieve and inject context
into agent prompts for enriching CV content.
"""
import logging
from typing import List, Optional

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

from backend.core.schema import CVData

logger = logging.getLogger(__name__)

ENRICH_PROMPT = PromptTemplate(
    input_variables=["context", "role", "company", "existing_bullets"],
    template="""You are an expert CV writer. Using the best-practice examples below,
enhance and rewrite the bullet points for a {role} position at {company}.

Best-practice examples from similar roles:
{context}

Existing bullets to improve:
{existing_bullets}

Rules:
- Start each bullet with a strong action verb (Led, Built, Delivered, Increased, Reduced, etc.)
- Quantify achievements where possible (e.g., "Reduced load time by 40%")
- Keep each bullet to 1-2 lines
- Return exactly 4-5 polished bullet points
- Output ONLY the bullet points, one per line, starting with "•"
"""
)

SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context", "name", "headline", "years_experience", "top_skills"],
    template="""You are an expert CV writer. Write a compelling 3-sentence professional summary.

Context and examples from similar profiles:
{context}

Candidate details:
- Name: {name}
- Role: {headline}
- Years of experience: {years_experience}
- Top skills: {top_skills}

Write a confident, achievement-focused summary. Output ONLY the summary paragraph, no preamble.
"""
)


class CVRAGEnricher:
    """Enriches CV content using RAG-retrieved best practices."""

    def __init__(
        self,
        chroma_persist_dir: str,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-large",
        llm_model: str = "gpt-4o",
    ):
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            openai_api_key=openai_api_key,
        )
        self.llm = ChatOpenAI(
            model=llm_model,
            openai_api_key=openai_api_key,
            temperature=0.4,
        )
        self.bullets_store = Chroma(
            collection_name="cv_bullet_examples",
            embedding_function=self.embeddings,
            persist_directory=chroma_persist_dir,
        )
        self.summaries_store = Chroma(
            collection_name="cv_summary_examples",
            embedding_function=self.embeddings,
            persist_directory=chroma_persist_dir,
        )
        logger.info("CVRAGEnricher initialised")

    async def enrich_bullets(
        self,
        role: str,
        company: str,
        existing_bullets: List[str],
        n_examples: int = 4,
    ) -> List[str]:
        """Retrieve similar bullets and rewrite with GPT-4o."""
        query = f"{role} achievements at technology company"
        docs = self.bullets_store.similarity_search(query, k=n_examples)
        context = "\n".join(d.page_content for d in docs)

        bullets_text = "\n".join(f"• {b}" for b in existing_bullets) if existing_bullets else "None provided"

        chain_input = ENRICH_PROMPT.format(
            context=context,
            role=role,
            company=company,
            existing_bullets=bullets_text,
        )

        from langchain_core.messages import HumanMessage
        response = await self.llm.ainvoke([HumanMessage(content=chain_input)])
        raw = response.content.strip()

        # Parse bullet lines
        bullets = []
        for line in raw.split("\n"):
            line = line.strip().lstrip("•-* ").strip()
            if line:
                bullets.append(line)
        return bullets[:5]

    async def generate_summary(self, cv_data: CVData) -> str:
        """Generate professional summary using RAG examples."""
        headline = cv_data.headline or "Professional"
        query = f"professional summary for {headline}"
        docs = self.summaries_store.similarity_search(query, k=3)
        context = "\n\n".join(d.page_content for d in docs)

        years = _estimate_years(cv_data)
        top_skills = ", ".join(cv_data.skills[:6]) if cv_data.skills else "various technical skills"

        chain_input = SUMMARY_PROMPT.format(
            context=context,
            name=cv_data.full_name or "the candidate",
            headline=headline,
            years_experience=years,
            top_skills=top_skills,
        )

        from langchain_core.messages import HumanMessage
        response = await self.llm.ainvoke([HumanMessage(content=chain_input)])
        return response.content.strip()


def _estimate_years(cv_data: CVData) -> str:
    if not cv_data.work_experience:
        return "several years"
    return f"{len(cv_data.work_experience) * 2}+"
