import os
import sys
import shutil
import datetime
from typing import Optional, List

# Ensure backend directory is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from document_processor import DocumentProcessor
from vector_store import VectorStore
from llm_provider import LLMProvider
from agents import AgentManager

app = FastAPI(title="Nexora – Intelligent Knowledge Workspace API", version="2.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories (Absolute paths)
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "../data/uploads"))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Initialize Core Services
doc_processor = DocumentProcessor()
vector_store = VectorStore()
llm_provider = LLMProvider()
agent_manager = AgentManager(vector_store, llm_provider)

# In-memory document registry
uploaded_docs = []

# Serve CSS and JS explicitly with proper MIME types
@app.get("/styles.css")
async def get_css():
    css_path = os.path.join(FRONTEND_DIR, "styles.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    raise HTTPException(status_code=404, detail="CSS not found")

@app.get("/app.js")
async def get_js():
    js_path = os.path.join(FRONTEND_DIR, "app.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="JS not found")

# Serve Frontend static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process document
        doc_result = doc_processor.process_file(file_path, file.filename)

        # Index chunks in Vector Database
        vector_store.add_chunks(doc_result["chunks"])

        uploaded_docs.append({
            "file_id": doc_result["file_id"],
            "filename": doc_result["filename"],
            "file_type": doc_result["file_type"],
            "total_pages": doc_result["total_pages"],
            "total_chunks": doc_result["total_chunks"],
            "uploaded_at": doc_result["uploaded_at"]
        })

        return JSONResponse({
            "status": "success",
            "message": f"Document '{file.filename}' processed & indexed into ChromaDB successfully.",
            "document": doc_result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.get("/api/documents")
async def list_documents():
    return JSONResponse({
        "total_documents": len(uploaded_docs),
        "documents": uploaded_docs,
        "vector_stats": vector_store.get_stats()
    })

@app.delete("/api/documents/{file_id}")
async def delete_document(file_id: str):
    global uploaded_docs
    doc_to_delete = next((d for d in uploaded_docs if d["file_id"] == file_id), None)
    if not doc_to_delete:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(UPLOAD_DIR, doc_to_delete["filename"])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    uploaded_docs = [d for d in uploaded_docs if d["file_id"] != file_id]
    vector_store.delete_chunks_by_file_id(file_id)

    return JSONResponse({
        "status": "success",
        "message": f"Document '{doc_to_delete['filename']}' deleted successfully."
    })

@app.delete("/api/documents")
async def clear_all_documents():
    global uploaded_docs
    for d in uploaded_docs:
        file_path = os.path.join(UPLOAD_DIR, d["filename"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
    uploaded_docs = []
    vector_store.clear_all()
    return JSONResponse({
        "status": "success",
        "message": "All documents deleted and vector database cleared."
    })


@app.post("/api/chat")
async def chat_with_agent(
    query: str = Form(...),
    agent: str = Form("auto"),
    file_id: Optional[str] = Form(None),
    file_ids: Optional[str] = Form(None)
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    file_ids_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()] if file_ids else None
    result = agent_manager.process_request(query=query, requested_agent=agent, file_id=file_id, file_ids=file_ids_list)
    return JSONResponse(result)

@app.post("/api/generate-podcast")
async def generate_podcast(file_ids: Optional[str] = Form(None)):
    file_ids_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()] if file_ids else None
    podcast_data = agent_manager.generate_podcast(file_ids=file_ids_list)
    return JSONResponse(podcast_data)

@app.post("/api/studio-artifact")
async def generate_studio_artifact(
    artifact_type: str = Form("briefing_doc"),
    file_ids: Optional[str] = Form(None)
):
    file_ids_list = [fid.strip() for fid in file_ids.split(",") if fid.strip()] if file_ids else None
    content = agent_manager.generate_studio_artifact(artifact_type, file_ids=file_ids_list)
    return JSONResponse({
        "status": "success",
        "artifact_type": artifact_type,
        "content": content
    })


@app.get("/api/system-status")
async def get_system_status():
    return JSONResponse({
        "status": "online",
        "system": "Nexora Agentic AI Workspace",
        "vector_engine": "ChromaDB / Native Vector Engine",
        "embedder": "SentenceTransformers (all-MiniLM-L6-v2)",
        "active_agents": ["DocumentAgent", "ResearchAgent", "SummaryAgent", "CitationAgent", "ReportAgent"],
        "llm_provider": "Free Tier Gemini / Groq / Smart Grounded Fallback Engine",
        "documents_count": len(uploaded_docs),
        "total_chunks": vector_store.get_stats()["total_chunks"]
    })

@app.post("/api/export-report")
async def export_report(
    report_title: str = Form("Nexora_Analysis_Report"),
    content: str = Form(...)
):
    try:
        report_filename = f"{report_title.replace(' ', '_')}.md"
        report_path = os.path.join(UPLOAD_DIR, report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        return JSONResponse({
            "status": "success",
            "message": "Report generated successfully.",
            "download_url": f"/api/download-file?filename={report_filename}"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-file")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/logo.png")
async def get_logo_file():
    logo_file = os.path.join(FRONTEND_DIR, "logo_transparent.png")
    if not os.path.exists(logo_file):
        logo_file = os.path.join(FRONTEND_DIR, "logo.png")
    if os.path.exists(logo_file):
        return FileResponse(logo_file)
    raise HTTPException(status_code=404, detail="Logo file not found")

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Nexora API running. Frontend loading...</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
