"""
EVO-TR Web API - Main Application

FastAPI application with all endpoints.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
import time
from pathlib import Path


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="EVO-TR API",
        description="Türkçe AI Asistan - Multi-Expert LoRA System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app


app = create_app()


# ============== Pydantic Models ==============

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    adapter: Optional[str] = None  # Auto-route if None
    stream: bool = False
    max_tokens: int = 512
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    intent: str
    adapter_used: str
    confidence: float
    tokens_generated: int
    generation_time: float


class MemorySearchRequest(BaseModel):
    """Memory search request model."""
    query: str
    limit: int = 5
    memory_type: Optional[str] = None  # conversation, fact, preference


class MemoryItem(BaseModel):
    """Memory item model."""
    id: str
    content: str
    memory_type: str
    timestamp: str
    relevance: float


class AdapterInfo(BaseModel):
    """Adapter info model."""
    name: str
    path: str
    intent: str
    description: str
    size_mb: float
    loaded: bool


class SystemStatus(BaseModel):
    """System status model."""
    status: str
    model_loaded: bool
    adapters_available: List[str]
    active_adapter: Optional[str]
    memory_usage_mb: float
    uptime_seconds: float


class FeedbackRequest(BaseModel):
    """Feedback request model."""
    message_id: str
    user_message: str
    assistant_response: str
    feedback_type: str  # thumbs_up, thumbs_down, edit, retry
    intent: Optional[str] = None
    adapter_used: Optional[str] = None
    confidence: Optional[float] = None
    category: Optional[str] = None  # For thumbs_down: incorrect, irrelevant, etc.
    comment: Optional[str] = None
    corrected_response: Optional[str] = None  # For edit feedback


class FeedbackResponse(BaseModel):
    """Feedback response model."""
    success: bool
    feedback_id: str
    message: str


# ============== Global State ==============

class AppState:
    """Application state management."""
    
    def __init__(self):
        self.start_time = time.time()
        self.orchestrator = None
        self.model_loaded = False
        self.active_connections: List[WebSocket] = []
        self.feedback_db = None
    
    async def initialize(self):
        """Initialize the orchestrator and model."""
        if self.orchestrator is None:
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from src.orchestrator import EvoTR
                from src.lifecycle.feedback import FeedbackDatabase
                
                self.orchestrator = EvoTR(
                    base_model_path="./models/base/qwen-2.5-3b-instruct",
                    adapters_dir="./adapters"
                )
                
                # Initialize feedback database
                self.feedback_db = FeedbackDatabase("./data/feedback.db")
                self.model_loaded = True
                print("✅ Orchestrator initialized")
            except Exception as e:
                print(f"❌ Failed to initialize orchestrator: {e}")
                self.model_loaded = False
    
    def get_uptime(self) -> float:
        return time.time() - self.start_time


state = AppState()


# ============== Startup/Shutdown ==============

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("🚀 EVO-TR API starting...")
    # Lazy loading - don't load model on startup
    # await state.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 EVO-TR API shutting down...")


# ============== REST Endpoints ==============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main chat UI."""
    ui_path = Path(__file__).parent / "static" / "index.html"
    if ui_path.exists():
        return ui_path.read_text(encoding="utf-8")
    return """
    <!DOCTYPE html>
    <html>
    <head><title>EVO-TR</title></head>
    <body>
        <h1>🤖 EVO-TR API</h1>
        <p>API is running. Visit <a href="/docs">/docs</a> for API documentation.</p>
        <p>Or visit <a href="/chat-ui">/chat-ui</a> for the chat interface.</p>
    </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/status", response_model=SystemStatus)
async def get_status():
    """Get system status."""
    import psutil
    
    adapters = []
    adapters_dir = Path("./adapters")
    if adapters_dir.exists():
        adapters = [d.name for d in adapters_dir.iterdir() if d.is_dir()]
    
    memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    
    return SystemStatus(
        status="running",
        model_loaded=state.model_loaded,
        adapters_available=adapters,
        active_adapter=None,
        memory_usage_mb=round(memory_mb, 2),
        uptime_seconds=round(state.get_uptime(), 2)
    )


@app.get("/adapters", response_model=List[AdapterInfo])
async def list_adapters():
    """List available adapters."""
    adapters = []
    adapters_dir = Path("./adapters")
    
    if not adapters_dir.exists():
        return adapters
    
    intent_descriptions = {
        "tr_chat": ("turkish_culture", "Türkçe sohbet ve kültür"),
        "tr_chat_v2": ("turkish_culture", "Türkçe sohbet v2"),
        "python_coder": ("code_python", "Python kod yazma ve debug"),
        "math_expert": ("code_math", "Matematik problem çözme"),
        "science_expert": ("science", "Fizik, Kimya, Biyoloji"),
        "history_expert": ("history", "Türk ve dünya tarihi"),
    }
    
    for adapter_dir in adapters_dir.iterdir():
        if adapter_dir.is_dir():
            adapter_file = adapter_dir / "adapters.safetensors"
            size_mb = 0
            if adapter_file.exists():
                size_mb = adapter_file.stat().st_size / (1024 * 1024)
            
            intent, desc = intent_descriptions.get(
                adapter_dir.name, 
                ("general", "General adapter")
            )
            
            adapters.append(AdapterInfo(
                name=adapter_dir.name,
                path=str(adapter_dir),
                intent=intent,
                description=desc,
                size_mb=round(size_mb, 2),
                loaded=False
            ))
    
    return adapters


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint.
    
    Sends a message and gets a response.
    If adapter is not specified, auto-routes based on intent.
    """
    # Initialize if needed
    if state.orchestrator is None:
        await state.initialize()
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        start_time = time.time()
        
        # Use orchestrator for routing and generation
        response = state.orchestrator.chat(
            message=request.message,
            force_adapter=request.adapter
        )
        
        # Get details from last conversation turn
        history = state.orchestrator.get_conversation_history()
        last_turn = history[-1] if history else None
        
        generation_time = time.time() - start_time
        
        return ChatResponse(
            response=response,
            intent=last_turn.intent if last_turn else "general_chat",
            adapter_used=last_turn.adapter_used or "base_model" if last_turn else "base_model",
            confidence=last_turn.confidence if last_turn else 0.0,
            tokens_generated=last_turn.tokens_generated if last_turn else 0,
            generation_time=round(generation_time, 3)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    
    Returns Server-Sent Events (SSE) stream with token-by-token generation.
    
    Event types:
    - meta: {type: 'meta', intent, confidence, adapter}
    - token: {type: 'token', text}
    - done: {type: 'done', tokens_generated, generation_time}
    - error: {type: 'error', message}
    """
    if state.orchestrator is None:
        await state.initialize()
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    async def generate():
        try:
            # Use real streaming from orchestrator
            for chunk in state.orchestrator.chat_stream(
                message=request.message,
                force_adapter=request.adapter
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
                # Small delay to prevent buffer issues
                await asyncio.sleep(0.01)
        
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """
    Search memory/RAG.
    
    Returns relevant memories based on query.
    """
    if state.orchestrator is None:
        await state.initialize()
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        # Use memory manager to search
        results = state.orchestrator.memory_manager.search(
            query=request.query,
            limit=request.limit,
            memory_type=request.memory_type
        )
        
        items = []
        for r in results:
            items.append(MemoryItem(
                id=r.get("id", ""),
                content=r.get("content", ""),
                memory_type=r.get("type", "unknown"),
                timestamp=r.get("timestamp", ""),
                relevance=r.get("relevance", 0.0)
            ))
        
        return {"results": items, "total": len(items)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/add")
async def add_memory(content: str, memory_type: str = "fact"):
    """Add a memory/fact."""
    if state.orchestrator is None:
        await state.initialize()
    
    if not state.model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        state.orchestrator.memory_manager.add_fact(content)
        return {"success": True, "message": "Memory added"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/intents")
async def list_intents():
    """List supported intents."""
    intents_file = Path("./configs/intent_mapping.json")
    if intents_file.exists():
        with open(intents_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "intents": list(data.get("intent_to_adapter", {}).keys()),
            "descriptions": data.get("intent_descriptions", {}),
            "total": len(data.get("intent_to_adapter", {}))
        }
    return {"intents": [], "descriptions": {}, "total": 0}


@app.get("/route")
async def route_message(message: str):
    """
    Route a message to determine intent.
    
    Returns intent and confidence without generating a response.
    """
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.router.api import route_with_details
        
        result = route_with_details(message)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== WebSocket ==============

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.
    
    Protocol:
    - Client sends: {"message": "...", "adapter": null}
    - Server sends: {"type": "meta", "intent": "...", "confidence": ..., "adapter": "..."}
    - Server sends: {"type": "token", "text": "..."} for each token
    - Server sends: {"type": "done", "tokens_generated": ..., "generation_time": ...}
    """
    await websocket.accept()
    state.active_connections.append(websocket)
    
    try:
        # Initialize if needed
        if state.orchestrator is None:
            await state.initialize()
        
        # Send connection status
        await websocket.send_json({
            "type": "connected",
            "model_loaded": state.model_loaded
        })
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            adapter = data.get("adapter")
            
            if not message:
                await websocket.send_json({"type": "error", "message": "Empty message"})
                continue
            
            try:
                # Use real streaming
                for chunk in state.orchestrator.chat_stream(
                    message=message,
                    force_adapter=adapter
                ):
                    await websocket.send_json(chunk)
                    await asyncio.sleep(0.01)  # Small delay for smooth streaming
            
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)
        print(f"WebSocket disconnected. Active: {len(state.active_connections)}")


# ============== Feedback Endpoints ==============

@app.post("/feedback/add", response_model=FeedbackResponse)
async def add_feedback(request: FeedbackRequest):
    """Add user feedback for a response."""
    await state.initialize()
    
    if state.feedback_db is None:
        raise HTTPException(status_code=500, detail="Feedback database not initialized")
    
    from src.lifecycle.feedback import FeedbackEntry
    import uuid
    
    # Create FeedbackEntry from request
    entry = FeedbackEntry(
        session_id=str(uuid.uuid4())[:8],  # Generate if not provided
        message_id=request.message_id,
        user_message=request.user_message,
        assistant_response=request.assistant_response,
        intent=request.intent or "",
        adapter_used=request.adapter_used or "",
        confidence=request.confidence or 0.0,
        feedback_type=request.feedback_type,
        feedback_category=request.category,
        comment=request.comment,
        corrected_response=request.corrected_response
    )
    
    feedback_id = state.feedback_db.add_feedback(entry)
    
    return FeedbackResponse(
        success=True,
        feedback_id=feedback_id,
        message=f"Feedback kaydedildi: {request.feedback_type}"
    )


@app.get("/feedback/stats")
async def get_feedback_stats():
    """Get feedback statistics."""
    await state.initialize()
    
    if state.feedback_db is None:
        raise HTTPException(status_code=500, detail="Feedback database not initialized")
    
    stats = state.feedback_db.get_stats()
    return stats


# ============== Monitoring Endpoints ==============

@app.get("/monitor/stats")
async def get_monitor_stats():
    """Get comprehensive monitoring statistics."""
    import psutil
    import sqlite3
    from datetime import datetime
    
    stats = {
        "timestamp": datetime.now().isoformat(),
        "server": {},
        "feedback": {},
        "memory": {},
        "adapters": [],
        "conversations": {}
    }
    
    # Server stats
    process = psutil.Process()
    stats["server"] = {
        "status": "running",
        "uptime_seconds": round(state.get_uptime(), 2),
        "process_memory_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "cpu_percent": process.cpu_percent(),
        "model_loaded": state.model_loaded,
        "active_websockets": len(state.active_connections)
    }
    
    # System memory
    mem = psutil.virtual_memory()
    stats["memory"] = {
        "total_gb": round(mem.total / (1024**3), 2),
        "used_gb": round(mem.used / (1024**3), 2),
        "available_gb": round(mem.available / (1024**3), 2),
        "percent": mem.percent
    }
    
    # Feedback stats
    feedback_db_path = Path("./data/feedback.db")
    if feedback_db_path.exists():
        try:
            conn = sqlite3.connect(str(feedback_db_path))
            cursor = conn.cursor()
            
            # Total feedback
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]
            
            # By type
            cursor.execute("""
                SELECT feedback_type, COUNT(*) 
                FROM feedback 
                GROUP BY feedback_type
            """)
            by_type = dict(cursor.fetchall())
            
            # Corrections
            cursor.execute("""
                SELECT COUNT(*) FROM feedback 
                WHERE corrected_response IS NOT NULL AND corrected_response != ''
            """)
            corrections = cursor.fetchone()[0]
            
            # Unprocessed
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE processed = 0")
            unprocessed = cursor.fetchone()[0]
            
            # Used for training
            cursor.execute("SELECT COUNT(*) FROM feedback WHERE used_for_training = 1")
            trained = cursor.fetchone()[0]
            
            # Recent feedback
            cursor.execute("""
                SELECT id, feedback_type, user_message, timestamp 
                FROM feedback 
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            recent = []
            for row in cursor.fetchall():
                recent.append({
                    "id": row[0][:8] if row[0] else "",
                    "type": row[1],
                    "message": (row[2][:50] + "...") if row[2] and len(row[2]) > 50 else row[2],
                    "timestamp": row[3]
                })
            
            conn.close()
            
            stats["feedback"] = {
                "total": total,
                "by_type": by_type,
                "corrections": corrections,
                "unprocessed": unprocessed,
                "trained": trained,
                "training_threshold": 10,
                "ready_for_training": corrections >= 10,
                "recent": recent
            }
        except Exception as e:
            stats["feedback"] = {"error": str(e)}
    
    # Adapters
    adapters_dir = Path("./adapters")
    if adapters_dir.exists():
        for adapter_path in adapters_dir.iterdir():
            if adapter_path.is_dir() and not adapter_path.name.startswith('.'):
                config_file = adapter_path / "adapter_config.json"
                size_mb = sum(f.stat().st_size for f in adapter_path.rglob('*') if f.is_file()) / (1024*1024)
                stats["adapters"].append({
                    "name": adapter_path.name,
                    "valid": config_file.exists(),
                    "size_mb": round(size_mb, 2),
                    "is_v2": "v2" in adapter_path.name
                })
    
    # Conversation stats (from logs)
    logs_dir = Path("./logs/conversations")
    if logs_dir.exists():
        total_conversations = 0
        today_conversations = 0
        today = datetime.now().strftime("%Y-%m-%d")
        
        for log_file in logs_dir.glob("*.jsonl"):
            if today in log_file.name:
                with open(log_file, "r") as f:
                    today_conversations = sum(1 for _ in f)
            with open(log_file, "r") as f:
                total_conversations += sum(1 for _ in f)
        
        stats["conversations"] = {
            "total": total_conversations,
            "today": today_conversations
        }
    else:
        # Try main logs directory
        main_log = Path(f"./logs/conversations_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
        if main_log.exists():
            with open(main_log, "r") as f:
                today_count = sum(1 for _ in f)
            stats["conversations"] = {"today": today_count, "total": today_count}
        else:
            stats["conversations"] = {"today": 0, "total": 0}
    
    return stats


@app.get("/monitor", response_class=HTMLResponse)
async def monitor_dashboard():
    """Serve monitoring dashboard."""
    dashboard_path = Path(__file__).parent / "static" / "monitor.html"
    if dashboard_path.exists():
        return dashboard_path.read_text(encoding="utf-8")
    return """
    <!DOCTYPE html>
    <html>
    <head><title>EVO-TR Monitor</title></head>
    <body>
        <h1>🖥️ EVO-TR Monitor</h1>
        <p>Dashboard file not found. Please create static/monitor.html</p>
    </body>
    </html>
    """


@app.post("/monitor/train")
async def trigger_training():
    """Trigger training manually."""
    import subprocess
    import sys
    
    try:
        result = subprocess.run(
            [sys.executable, "./scripts/process_feedback.py", "--train"],
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== Static Files ==============

# Mount static files if directory exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
