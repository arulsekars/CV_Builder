"""
RAG Data Ingestion Pipeline
────────────────────────────
Seeds ChromaDB with CV best-practice examples.
Run once before starting the server: python -m backend.rag.ingest
"""
import logging
import sys
from pathlib import Path

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Seed Data ────────────────────────────────────────────────
# Production: load from JSON/CSV files in data/sample_cvs/
# Here we embed representative examples inline.

BULLET_EXAMPLES = [
    # Engineering
    Document(page_content="Led migration of monolithic application to microservices, reducing deployment time by 65% and improving system reliability to 99.9% uptime.", metadata={"role": "software engineer", "industry": "tech"}),
    Document(page_content="Built CI/CD pipeline using GitHub Actions and Docker, cutting release cycle from 2 weeks to 2 days.", metadata={"role": "software engineer", "industry": "tech"}),
    Document(page_content="Delivered RESTful API serving 5M+ requests/day with <100ms P99 latency using FastAPI and Redis caching.", metadata={"role": "software engineer", "industry": "tech"}),
    Document(page_content="Architected event-driven data pipeline processing 10TB/day using Apache Kafka and Apache Spark.", metadata={"role": "data engineer", "industry": "tech"}),
    Document(page_content="Reduced cloud infrastructure costs by 40% through right-sizing EC2 instances and implementing auto-scaling policies.", metadata={"role": "cloud engineer", "industry": "tech"}),
    Document(page_content="Mentored team of 6 junior engineers, running weekly code reviews and pairing sessions, increasing team velocity by 30%.", metadata={"role": "senior engineer", "industry": "tech"}),
    Document(page_content="Implemented machine learning model for customer churn prediction achieving 87% accuracy, saving £2M in annual revenue.", metadata={"role": "data scientist", "industry": "tech"}),
    Document(page_content="Drove adoption of Infrastructure as Code (Terraform), eliminating manual provisioning errors and reducing environment setup from 3 days to 2 hours.", metadata={"role": "devops", "industry": "tech"}),
    # Management
    Document(page_content="Managed cross-functional team of 12 across 3 time zones, delivering £5M project on time and 8% under budget.", metadata={"role": "project manager", "industry": "consulting"}),
    Document(page_content="Established OKR framework across 4 product teams, improving alignment and increasing on-time delivery rate from 58% to 84%.", metadata={"role": "product manager", "industry": "tech"}),
    Document(page_content="Negotiated £1.2M SaaS contracts with enterprise clients, achieving 95% renewal rate through quarterly business reviews.", metadata={"role": "account manager", "industry": "sales"}),
    Document(page_content="Redesigned onboarding process reducing time-to-productivity for new hires from 6 weeks to 3 weeks.", metadata={"role": "hr manager", "industry": "hr"}),
    # Finance
    Document(page_content="Developed financial models forecasting £50M revenue over 5-year horizon with 92% YoY accuracy.", metadata={"role": "financial analyst", "industry": "finance"}),
    Document(page_content="Conducted due diligence on 8 M&A targets, identifying £3.2M in synergies that informed board decision to proceed.", metadata={"role": "analyst", "industry": "finance"}),
    # Marketing
    Document(page_content="Launched integrated digital marketing campaign generating 45% increase in qualified leads at 22% lower cost-per-acquisition.", metadata={"role": "marketing manager", "industry": "marketing"}),
    Document(page_content="Grew organic search traffic by 180% in 12 months through content strategy and technical SEO improvements.", metadata={"role": "seo specialist", "industry": "marketing"}),
]

SUMMARY_EXAMPLES = [
    Document(page_content="Results-driven Senior Software Engineer with 8+ years building scalable distributed systems in Python and Go. Proven track record delivering high-availability services processing millions of transactions daily. Passionate about clean architecture, mentoring engineering teams, and driving adoption of DevOps best practices.", metadata={"role": "senior software engineer"}),
    Document(page_content="Strategic Product Manager with 6 years translating complex customer problems into market-winning products. Expert in agile methodologies, cross-functional leadership, and data-driven decision making. Delivered £12M in ARR growth through a portfolio of B2B SaaS products in the fintech sector.", metadata={"role": "product manager"}),
    Document(page_content="Data Scientist specialising in NLP and predictive analytics with 4 years at the intersection of machine learning research and business impact. Proficient in Python, PyTorch, and Spark. Published author with a proven ability to communicate complex models to non-technical stakeholders.", metadata={"role": "data scientist"}),
    Document(page_content="Dynamic Marketing Director with 10+ years building brand strategies for FTSE 250 companies. Expert in integrated digital marketing, performance analytics, and agency management. Consistently delivered 30%+ YoY growth in pipeline contribution.", metadata={"role": "marketing director"}),
    Document(page_content="Experienced Project Manager (PMP, Prince2) with a 95% on-time delivery record across infrastructure and digital transformation programmes up to £8M. Skilled in stakeholder management, risk mitigation, and Agile/Waterfall hybrid delivery.", metadata={"role": "project manager"}),
    Document(page_content="Cloud Solutions Architect with 7 years designing enterprise-grade AWS and Azure infrastructure. Certified AWS Solutions Architect Professional. Reduced average cloud spend by 35% while improving system reliability and security posture for global financial services clients.", metadata={"role": "cloud architect"}),
]


def ingest(persist_dir: str, openai_api_key: str, embedding_model: str = "text-embedding-3-large"):
    """Ingest seed data into ChromaDB."""
    logger.info("Starting RAG data ingestion...")

    embeddings = OpenAIEmbeddings(
        model=embedding_model,
        openai_api_key=openai_api_key,
    )

    # Ingest bullet examples
    logger.info(f"Ingesting {len(BULLET_EXAMPLES)} bullet examples...")
    bullets_store = Chroma(
        collection_name="cv_bullet_examples",
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    bullets_store.add_documents(BULLET_EXAMPLES)
    logger.info(f"  ✓ Bullets collection: {bullets_store._collection.count()} documents")

    # Ingest summary examples
    logger.info(f"Ingesting {len(SUMMARY_EXAMPLES)} summary examples...")
    summaries_store = Chroma(
        collection_name="cv_summary_examples",
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    summaries_store.add_documents(SUMMARY_EXAMPLES)
    logger.info(f"  ✓ Summaries collection: {summaries_store._collection.count()} documents")

    logger.info("✅ RAG ingestion complete!")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set in environment")
        sys.exit(1)

    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")

    ingest(persist_dir, api_key, embedding_model)
