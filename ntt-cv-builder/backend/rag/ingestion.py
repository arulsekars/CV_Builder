"""
rag/ingestion.py
Seeds the ChromaDB knowledge base with CV examples and best-practice content.
Run once: python -m rag.ingestion
"""
from __future__ import annotations
import os
import json
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from config import get_settings

settings = get_settings()

# Sample CV best-practice content for the knowledge base
# In production, load from data/cv_examples/ directory
SAMPLE_KNOWLEDGE = [
    {
        "content": """Software Engineer bullet points - Technology sector:
• Architected and delivered a microservices migration reducing system latency by 40%
• Led a team of 5 engineers to ship a real-time data pipeline processing 2M events/day
• Reduced CI/CD pipeline runtime by 60% through parallelisation and caching strategies
• Implemented automated testing suite achieving 92% code coverage across 3 repositories
• Mentored 3 junior engineers, 2 of whom were promoted within 12 months""",
        "metadata": {"role": "software_engineer", "industry": "technology", "type": "bullets"},
    },
    {
        "content": """Data Scientist bullet points - Technology / Finance sector:
• Built ML classification model achieving 94% accuracy on fraud detection dataset (8M records)
• Reduced customer churn by 18% using predictive modelling and targeted intervention campaigns
• Automated monthly reporting pipeline saving 40 analyst-hours per month
• Deployed NLP sentiment analysis model processing 500K customer reviews daily
• Collaborated with product team to A/B test 12 feature experiments, driving 22% engagement lift""",
        "metadata": {"role": "data_scientist", "industry": "technology", "type": "bullets"},
    },
    {
        "content": """Project Manager bullet points - Consulting / Technology:
• Delivered £2.4M ERP implementation on time and 8% under budget across 4 business units
• Managed cross-functional team of 18 stakeholders across 3 time zones
• Reduced project reporting time by 35% through introduction of automated dashboards
• Achieved 100% client satisfaction rating across 6 consecutive project deliveries
• Implemented agile transformation resulting in 30% faster feature delivery cycles""",
        "metadata": {"role": "project_manager", "industry": "consulting", "type": "bullets"},
    },
    {
        "content": """Marketing Manager bullet points - Consumer / Digital:
• Grew organic search traffic by 180% in 12 months through SEO-led content strategy
• Managed £500K paid media budget achieving 3.2x ROAS across Google and Meta channels
• Launched product campaign reaching 2.4M impressions and generating 12,000 qualified leads
• Built email nurture programme increasing conversion rate from 2.1% to 5.8%
• Led rebranding initiative across 14 markets, delivering assets 2 weeks ahead of schedule""",
        "metadata": {"role": "marketing_manager", "industry": "consumer", "type": "bullets"},
    },
    {
        "content": """Professional Summary examples - Technology:
Accomplished Software Engineer with 8+ years building scalable distributed systems in cloud environments.
Expert in Python, Go, and Kubernetes with a track record of delivering high-impact projects at pace.
Passionate about engineering excellence and mentoring high-performing teams.

Results-driven Data Scientist with expertise in machine learning, NLP, and large-scale data pipelines.
Proven ability to translate complex analytical insights into actionable business outcomes.
Strong communicator who bridges the gap between technical and non-technical stakeholders.""",
        "metadata": {"role": "technology", "type": "summary"},
    },
    {
        "content": """Professional Summary examples - Finance / Consulting:
Strategic Finance Manager with 10+ years in financial planning, analysis, and business partnering.
Expert in building robust financial models and communicating commercial insight to C-suite stakeholders.
Track record of driving cost efficiency and revenue growth in complex, matrixed organisations.

Senior Consultant with expertise in digital transformation and operational excellence.
Delivered £50M+ in client value across retail, financial services, and public sector engagements.
Known for building trusted client relationships and leading teams through complex change programmes.""",
        "metadata": {"role": "finance_consulting", "type": "summary"},
    },
    {
        "content": """Skills sections best practices:
Technical Skills: List specific technologies, tools, and platforms rather than vague terms.
Good: "Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS (EC2, S3, Lambda)"
Bad: "Databases, cloud, coding"

Soft Skills: Use evidence-based language tied to outcomes.
Good: "Cross-functional stakeholder management — led 18-person team across 3 time zones"
Bad: "Good communicator, team player"

Certifications to highlight in tech: AWS Solutions Architect, GCP Professional, Azure Administrator,
Kubernetes CKA, PMP, Scrum Master, CISSP, Google Analytics, Salesforce Admin""",
        "metadata": {"type": "skills_guidance"},
    },
    {
        "content": """CV structure best practices - NTT Data guidelines:
1. Contact: Name, email, phone, LinkedIn, location (city/country only, no full address)
2. Professional Summary: 2-4 sentences, tailored to target role, quantified where possible
3. Work Experience: reverse chronological, 3-5 bullets per role, action verbs, metrics
4. Education: degree, institution, year, grade (if strong)
5. Skills: grouped by category (Technical, Management, Languages, Certifications)
6. Keep to 2 pages max for <10 years experience, 3 pages for senior roles
7. Use active voice: "Led", "Delivered", "Built", not "Responsible for" or "Worked on"
8. Quantify everything possible: %, £, time saved, team size, scale""",
        "metadata": {"type": "guidelines"},
    },
]


def seed_knowledge_base() -> None:
    """Seed ChromaDB with the CV knowledge base. Safe to re-run (skips if already seeded)."""
    persist_dir = settings.chroma_persist_dir
    collection_name = "cv_knowledge"

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
    )

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )

    # Skip if already seeded
    existing = vectorstore.get()
    if len(existing.get("ids", [])) >= len(SAMPLE_KNOWLEDGE):
        print(f"Knowledge base already seeded with {len(existing['ids'])} chunks. Skipping.")
        return

    print(f"Seeding {len(SAMPLE_KNOWLEDGE)} knowledge items into ChromaDB...")

    texts = []
    metadatas = []
    for item in SAMPLE_KNOWLEDGE:
        chunks = splitter.split_text(item["content"])
        for chunk in chunks:
            texts.append(chunk)
            metadatas.append(item["metadata"])

    vectorstore.add_texts(texts=texts, metadatas=metadatas)
    print(f"✅ Seeded {len(texts)} chunks into ChromaDB at {persist_dir}")


def ingest_cv_examples_from_directory(directory: str = "data/cv_examples") -> None:
    """
    Load additional CV example files from a directory.
    Supports .txt and .json files.
    """
    path = Path(directory)
    if not path.exists():
        print(f"Directory {directory} not found, skipping.")
        return

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key,
    )
    vectorstore = Chroma(
        collection_name="cv_knowledge",
        embedding_function=embeddings,
        persist_directory=settings.chroma_persist_dir,
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)

    for file in path.glob("*.txt"):
        text = file.read_text()
        chunks = splitter.split_text(text)
        vectorstore.add_texts(
            texts=chunks,
            metadatas=[{"source": file.name, "type": "cv_example"}] * len(chunks),
        )
        print(f"  Ingested {file.name} — {len(chunks)} chunks")


if __name__ == "__main__":
    seed_knowledge_base()
    ingest_cv_examples_from_directory()
