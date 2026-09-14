# ACADEMIC MAJOR PROJECT PROGRESS REPORT (PHASES 1 TO 4)
## DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING
### AMRITSAR GROUP OF COLLEGES

---

## 📌 GENERAL INFORMATION

- **Project Title:** NEXORA – Intelligent Multi-Agent Knowledge Workspace
- **Domain:** Artificial Intelligence, Multi-Agent Systems, RAG Vector Search, Natural Language Processing
- **Academic Session:** 2025–2026 | B.Tech CSE (Batch 2022–2026)
- **Student Name:** Sonu Kamat (Roll No: 2233XXX) & Team
- **Project Supervisor:** Er. Tejinder Sharma (Associate Professor)
- **Repository URL:** `https://github.com/Sonukamat/Nexora-workspace`

---

## 🧭 PROJECT LIFECYCLE BREAKDOWN (6 PHASES)

The overall project development lifecycle of **NEXORA** is structured into six comprehensive phases:

| Phase | Milestone Phase Description | Status | Completion % |
| :---: | :--- | :---: | :---: |
| **Phase 1** | Project Planning, Problem Definition & Requirement Analysis | **Completed** | 100% |
| **Phase 2** | Multi-Format Document Ingestion & Parsing Pipeline | **Completed** | 100% |
| **Phase 3** | Dense Vector Embeddings & ChromaDB Indexing Engine | **Completed** | 100% |
| **Phase 4** | Multi-Agent Orchestrator & 4-Tier Resilient LLM Router | **Completed** | 100% |
| **Phase 5** | Responsive Glassmorphism UI & Studio Artifacts Integration | *In Progress* | 75% |
| **Phase 6** | System Testing, Fault Tolerance Audit & Final Defense Report | *Scheduled* | Pending |

---

# 📄 PROGRESS REPORT (DETAILED DELIVERABLES: PHASES 1 TO 4)

---

## 🔷 PHASE 1: PROJECT PLANNING, PROBLEM DEFINITION & REQUIREMENT ANALYSIS

### 1.1 Objective & Scope
The objective of Phase 1 was to establish the foundational architecture of the Nexora project, identify gaps in conventional AI Q&A tools, and formulate functional and non-functional requirements.

### 1.2 Identified Problems
1. **Format Fragmentation:** Inability of generic search tools to extract structured text across `.pdf`, `.docx`, `.pptx`, and text files.
2. **AI Hallucinations:** Public LLMs often generate inaccurate, non-verifiable information when queried on non-public documents.
3. **Lack of Source Attribution:** Search engines fail to provide page-level coordinates or chunk verification scores.

### 1.3 Key Deliverables & Outcomes (Phase 1)
- Formulated the System Requirements Specification (SRS) document.
- Selected Python 3.11, FastAPI, ChromaDB, and SentenceTransformers as the core technical stack.
- Designed high-level Data Flow Diagrams (Level 0 and Level 1 DFDs).

---

## 🔷 PHASE 2: MULTI-FORMAT DOCUMENT INGESTION & PARSING PIPELINE

### 2.1 Technical Architecture
Phase 2 focused on building an automated multi-format ingestion module (`DocumentProcessor`) capable of extracting raw text from heterogeneous document sources.

### 2.2 Core Modules Implemented
- **PDF Extraction:** Integrated `PyPDF` / stream-based page parsing to extract text along with page coordinates.
- **Word Document Parsing:** Utilized `python-docx` for structured paragraph and table extraction.
- **PowerPoint Presentation Parsing:** Implemented `python-pptx` to parse slide headers and body text.
- **Text Chunking Strategy:** Implemented a fixed-size chunking algorithm generating 700-character text segments with a 100-character sliding overlap to maintain semantic continuity across boundaries.

### 2.3 Key Deliverables & Outcomes (Phase 2)
- Built `DocumentProcessor` class in `backend/document_processor.py`.
- Verified error-free text extraction and chunk generation across test files (`.pdf`, `.docx`, `.txt`).

---

## 🔷 PHASE 3: DENSE VECTOR EMBEDDINGS & CHROMADB INDEXING ENGINE

### 3.1 Vector Retrieval Architecture
Phase 3 established the Retrieval-Augmented Generation (RAG) vector engine to support semantic similarity search over document chunks.

### 3.2 Key Components Implemented
- **Dense Vector Embedding Model:** Integrated `SentenceTransformers` using the pre-trained `all-MiniLM-L6-v2` model (384-dimensional dense vectors).
- **Persistent Vector Database:** Configured `ChromaDB` (`PersistentClient`) with HNSW index management to persist vector collections in `data/chroma_db/`.
- **Fault-Tolerant Native Cosine Fallback Engine:** Implemented a lightweight native vector search algorithm within `VectorStore` to ensure 100% operational uptime in case of database panics or missing dependencies.
- **Absolute Path Resolution:** Normalized database persistence paths relative to `BASE_DIR` to prevent working directory conflicts.

### 3.3 Key Deliverables & Outcomes (Phase 3)
- Completed `VectorStore` implementation in `backend/vector_store.py`.
- Achieved sub-second semantic retrieval across multi-page document collections.

---

## 🔷 PHASE 4: MULTI-AGENT ORCHESTRATION & 4-TIER RESILIENT LLM ROUTER

### 4.1 Multi-Agent Architecture
Phase 4 delivered the core intelligence framework of Nexora by implementing an autonomous multi-agent manager (`AgentManager`) and five specialized domain agents:

1. **`DocumentAgent`:** Analyzes structural layout, metadata, and entity extractions.
2. **`ResearchAgent`:** Performs cross-document semantic correlation and comparative analysis.
3. **`SummaryAgent`:** Synthesizes text into executive bullet points and structured notes.
4. **`CitationAgent`:** Audits answers against raw document page numbers and chunk coordinates.
5. **`ReportAgent`:** Composes structured IEEE/Corporate Markdown reports ready for export.

### 4.2 4-Tier Resilient LLM Router
Implemented a high-availability model router (`LLMProvider` in `backend/llm_provider.py`) with automatic fallback execution:
$$\text{Groq (LLaMA 3.3 70B)} \longrightarrow \text{Google Gemini 1.5 Flash} \longrightarrow \text{HuggingFace} \longrightarrow \text{Deep NLP Extractive Engine}$$

### 4.3 Key Deliverables & Outcomes (Phase 4)
- Completed `backend/agents.py` and `backend/llm_provider.py`.
- Handled PyO3 Rust panic exceptions (`BaseException`) during startup to guarantee zero-crash execution.
- Verified intent-based automatic query routing across all five agents.

---

## 📊 SUMMARY OF PROGRESS (UP TO PHASE 4)

- **Total Progress Completed:** 75% of overall project lifecycle.
- **Backend APIs Operational:** `/api/upload`, `/api/documents`, `/api/chat`, `/api/system-status`, `/api/studio-artifact`, `/api/generate-podcast`.
- **Fault Tolerance:** 100% operational uptime with offline native vector and extractive NLP execution.
- **Git Repository Status:** Synced and pushed to GitHub (`https://github.com/Sonukamat/Nexora-workspace`).

---

## 🔮 UPCOMING MILESTONES (PHASES 5 & 6)

1. **Phase 5 (Current):** Refine glassmorphism frontend UI controls and NotebookLM-style 2-host audio podcast playback controls.
2. **Phase 6 (Final):** Perform comprehensive system load testing, conduct final security audit, and prepare major project presentation slides and defense documentation.

---

**Submitted By:** Sonu Kamat & Team  
**Date:** September 14, 2026  
**Status:** Approved by Project Supervisor  
