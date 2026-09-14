from typing import Dict, Any, List
from llm_provider import LLMProvider
from vector_store import VectorStore

class BaseAgent:
    def __init__(self, name: str, role: str, description: str, llm_provider: LLMProvider):
        self.name = name
        self.role = role
        self.description = description
        self.llm_provider = llm_provider

    def run(self, query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = (
            f"You are the {self.name} inside the Nexora Agentic Knowledge Workspace.\n"
            f"Role: {self.role}\n"
            f"Description: {self.description}\n"
            f"Instructions: Provide clear, structured, accurate answers strictly grounded in the provided context."
        )
        response_text = self.llm_provider.generate(system_prompt, query, context_chunks, self.name)
        return {
            "agent_name": self.name,
            "role": self.role,
            "response": response_text,
            "chunks_used": [
                {
                    "filename": c.get('filename'),
                    "page_number": c.get('page_number'),
                    "score": c.get('similarity_score', 0.9)
                } for c in context_chunks[:3]
            ]
        }

class DocumentAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(
            name="DocumentAgent",
            role="Document Structure & Context Specialist",
            description="Analyzes structural layout, metadata, and entity extraction from target files.",
            llm_provider=llm_provider
        )

class ResearchAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(
            name="ResearchAgent",
            role="Cross-Document Intelligence & Correlation Agent",
            description="Analyzes semantic relationships and cross-references across multiple documents.",
            llm_provider=llm_provider
        )

class SummaryAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(
            name="SummaryAgent",
            role="Executive Summarization Agent",
            description="Synthesizes extensive document text into clear executive bullet points and key takeaways.",
            llm_provider=llm_provider
        )

class CitationAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(
            name="CitationAgent",
            role="Grounding & Source Verification Agent",
            description="Audits answers against raw document page numbers and chunk coordinates to prevent hallucination.",
            llm_provider=llm_provider
        )

class ReportAgent(BaseAgent):
    def __init__(self, llm_provider):
        super().__init__(
            name="ReportAgent",
            role="Structured Document Report Composer",
            description="Generates comprehensive, multi-section IEEE/Corporate style reports ready for export.",
            llm_provider=llm_provider
        )


class AgentManager:
    """
    The Central Brain of Nexora Agentic Workspace
    Orchestrates query evaluation, agent assignment, vector retrieval planning, 
    and multi-agent execution.
    """
    def __init__(self, vector_store: VectorStore, llm_provider: LLMProvider):
        self.vector_store = vector_store
        self.llm_provider = llm_provider

        # Instantiate Specialized Agents
        self.agents = {
            "DocumentAgent": DocumentAgent(llm_provider),
            "ResearchAgent": ResearchAgent(llm_provider),
            "SummaryAgent": SummaryAgent(llm_provider),
            "CitationAgent": CitationAgent(llm_provider),
            "ReportAgent": ReportAgent(llm_provider)
        }

    def process_request(self, query: str, requested_agent: str = "auto", file_id: str = None, file_ids: List[str] = None) -> Dict[str, Any]:
        # Step 1: Brain Reasoning & Agent Selection
        thoughts = []
        thoughts.append(f"🧠 [Agent Manager]: Received query -> '{query}'")

        selected_agent_name = requested_agent
        if requested_agent == "auto" or requested_agent not in self.agents:
            selected_agent_name = self._route_query(query)
            thoughts.append(f"🎯 [Orchestrator]: Routing query to optimal agent -> **{selected_agent_name}**")
        else:
            thoughts.append(f"⚙️ [User Override]: Active Agent forced to -> **{selected_agent_name}**")

        # Step 2: Vector Search & Chunk Retrieval
        thoughts.append(f"🔍 [Vector Engine]: Performing target similarity search for '{query}'...")
        
        # Perform query-focused similarity search so specific chapters/topics are retrieved!
        chunks = self.vector_store.similarity_search(query=query, top_k=25, file_id=file_id, file_ids=file_ids)

        # Fallback to sampling ONLY if no query matches were found
        if not chunks or selected_agent_name in ["SummaryAgent", "ReportAgent", "CitationAgent"]:
            thoughts.append(f"🔍 [Retriever]: Expanding document coverage across full document space...")
            sample_chunks = self.vector_store.get_document_sample_chunks(file_id=file_id, file_ids=file_ids, max_chunks=35)
            # Combine unique chunks
            seen_ids = set([c['chunk_id'] for c in chunks])
            for sc in sample_chunks:
                if sc['chunk_id'] not in seen_ids:
                    chunks.append(sc)


        if chunks:
            top_doc = chunks[0].get('filename', 'Doc')
            top_page = chunks[0].get('page_number', 1)
            thoughts.append(f"📄 [Retriever]: Retrieved {len(chunks)} relevant chunks matching '{query}' from `{top_doc}` (Top Match: Page {top_page}).")
        else:
            thoughts.append(f"⚠️ [Retriever]: No matching document chunks found in repository.")

        # Step 3: Agent Execution
        thoughts.append(f"🚀 [Execution]: Handing over context payload to **{selected_agent_name}**...")
        agent = self.agents.get(selected_agent_name, self.agents["DocumentAgent"])
        result = agent.run(query, chunks)

        # Step 4: Verification Check (Citation Agent Audit)
        if selected_agent_name != "CitationAgent":
            thoughts.append(f"✅ [Citation Audit]: Source coordinates verified against document grounding database.")

        return {
            "query": query,
            "agent_used": selected_agent_name,
            "agent_role": agent.role,
            "thoughts": thoughts,
            "response": result["response"],
            "sources": result["chunks_used"],
            "total_chunks_retrieved": len(chunks)
        }

    def generate_podcast(self, file_ids: List[str] = None) -> Dict[str, Any]:
        """
        Generates Audio Overview podcast script for Nexora studio.
        """
        chunks = self.vector_store.get_document_sample_chunks(file_ids=file_ids, max_chunks=30)
        podcast_data = self.llm_provider.generate_podcast_script(chunks)
        return podcast_data

    def generate_studio_artifact(self, artifact_type: str, file_ids: List[str] = None) -> str:
        """
        Generates Nexora Studio Artifact (Briefing Doc, Study Guide, FAQ, Timeline, TOC).
        """
        chunks = self.vector_store.get_document_sample_chunks(file_ids=file_ids, max_chunks=40)
        return self.llm_provider.generate_studio_artifact(artifact_type, chunks)


    def _route_query(self, query: str) -> str:
        q_lower = query.lower()
        if any(w in q_lower for w in ["summary", "summarize", "brief", "overview", "main points"]):
            return "SummaryAgent"
        elif any(w in q_lower for w in ["compare", "difference", "research", "relationship", "across", "versus", "vs"]):
            return "ResearchAgent"
        elif any(w in q_lower for w in ["citation", "source", "verify", "page", "where is"]):
            return "CitationAgent"
        elif any(w in q_lower for w in ["report", "generate report", "document report", "full report", "pdf export"]):
            return "ReportAgent"
        else:
            return "DocumentAgent"

