# MindGraph-RAG

**An explainable hybrid GraphRAG system for clinical reasoning, combining structured case extraction, DSM-5 knowledge graph constraints, and evidence-grounded literature retrieval to support transparent diagnostic decision-making.**

## Problem & Solution

Traditional linear RAG pipelines often fail on clinical cases that require **multi-hop reasoning** and strict **exclusion criteria** checks. When retrieval quality drops, downstream reasoning can collapse. MindGraph-RAG addresses this by combining vector search with graph-based clinical rules: case data is first structured, then routed to parallel retrieval paths (literature + DSM-5 graph), and finally synthesized through traceable multi-agent reasoning so experts can inspect how conclusions are formed.

## Architecture

Core pipeline (high level):

1. **Case Input (UI)**
2. **PII Masking & Structured Extraction (JSON)**
3. **Query Builder / Routing Layer**
4. **Parallel Retrieval**
   - Vector DB retrieval for literature and evidence
   - Graph DB retrieval for DSM-5 hierarchy and exclusion rules
5. **Multi-Agent Reasoning (Extractor -> Retriever -> Critic)**
6. **Transparent Reasoning Trace in UI**
7. **Final Synthesized Clinical Report**

## Tech Stack

- **Orchestration / LLM App Framework:** LangChain
- **Graph Layer:** Neo4j (DSM-5 rule modeling and traversal)
- **Vector Layer:** Chroma or Pinecone
- **UI / Demo App:** Streamlit
- **Retrieval Strategy:** Hybrid retrieval (BM25 + dense vectors)
- **Evaluation:** Ragas / G-Eval (hallucination and quality checks)
- **Data Safety:** PII masking and schema-constrained extraction

## Roadmap (14-Day Agile Micro-Sprints)

- [x] **Sprint 0 (Days 1-2) - Setup**
  - Initialize repository and environment
  - Prepare baseline Streamlit scaffold
- [ ] **Sprint 1 (Days 3-5) - Structured Intake**
  - JSON extraction from clinical cases
  - PII masking + simple baseline LLM response
  - Basic UI trace toggle
- [ ] **Sprint 2 (Days 6-8) - Hybrid Retrieval**
  - Query builder + BM25/vector integration
  - Citation support for retrieved evidence
- [ ] **Sprint 3 (Days 9-10) - Knowledge Graph & Parallel Retrieval**
  - DSM-5 graph layer and exclusion criteria checks
  - Parallel retrieval flow with visible intermediate outputs
- [ ] **Sprint 4 (Days 11-12) - Multi-Agent Orchestration**
  - Extractor / Retriever / Critic loop
  - Step-by-step reasoning trace in Streamlit
- [ ] **Sprint 5 (Days 13-14) - Production & Evaluation**
  - Hallucination control and prompt optimization
  - Evaluation dashboards/metrics and release-ready polish

## Vision

MindGraph-RAG is designed as a **clinical decision-support collaborator**, not a replacement for experts. Its goal is to improve speed, consistency, and evidence transparency while keeping human oversight central to every diagnostic interpretation.
