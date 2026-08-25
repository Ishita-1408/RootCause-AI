\# RootCause AI - Development Instructions



\## Project



RootCause AI is an autonomous business investigation platform.



The goal is to investigate business questions such as:



"Why did revenue decline?"



The system must provide evidence-backed explanations rather than unsupported AI guesses.



\---



\# Technology Direction



Primary backend language:



Python



Planned backend:



FastAPI



Planned frontend:



Next.js + TypeScript



Primary database:



Supabase PostgreSQL



Analytical engine:



DuckDB



Data processing:



Polars / Pandas / PyArrow



Machine learning:



scikit-learn / statsmodels



Testing:



pytest



Code quality:



Ruff / mypy



\---



\# Critical Architecture Rule



The LLM is NOT the source of numerical truth.



Important business calculations must be performed by deterministic:



\- SQL

\- Python

\- statistical

\- machine learning



components.



The LLM may:



\- understand questions

\- plan investigations

\- select tools

\- generate hypotheses

\- interpret results

\- explain evidence



The LLM must NOT invent numerical evidence.



\---



\# Development Philosophy



Build the project incrementally.



Only implement the phase explicitly requested.



Do NOT implement future phases unless asked.



Do NOT introduce unnecessary infrastructure.



Prefer simple architecture over premature complexity.



\---



\# Data Rules



Every analytical table must have a clearly defined grain.



Example:



fact\_order = one row per order



fact\_order\_item = one row per order item



Never create joins that silently duplicate revenue.



All important metrics must have explicit definitions.



\---



\# Agent Rules



Future AI agents must:



\- use typed tools

\- use structured outputs

\- have execution limits

\- have investigation-step limits

\- persist investigation state

\- never invent evidence

\- never claim causation from correlation alone



\---



\# Security Rules



Never expose secrets in frontend code.



Never commit:



.env



API keys



database secrets



Supabase service-role credentials



\---



\# Code Quality



Use:



\- type hints

\- Pydantic

\- pytest

\- Ruff

\- mypy



Tests should be added with meaningful functionality.



\---



\# Current Phase



Phase 0 - Project Foundation



At this stage DO NOT implement:



\- AI agents

\- LLM integration

\- Supabase schema

\- Olist ingestion

\- analytics

\- machine learning

\- root-cause analysis

\- dashboards



Only implement what is explicitly requested.

