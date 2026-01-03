"""
TheraBot SaaS - FastAPI Backend Main Application
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import uvicorn

from safety import SafetyChecker, CrisisResponse
from memory import MemoryManager, UserSession
from therapist import TherapistEngine, ChatResponse

# Initialize FastAPI app
app = FastAPI(
    title="TheraBot SaaS API",
    description="AI Therapy Assistant with Safety Protocols",
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

# Security
security = HTTPBearer()

# Initialize modules
safety_checker = SafetyChecker()
memory_manager = MemoryManager()
therapist_engine = TherapistEngine()

# Pydantic Models
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponseModel(BaseModel):
    message: str
    session_id: str
    timestamp: datetime
    is_crisis: bool = False
    safety_level: str = "safe"
    crisis_resources: Optional[List[str]] = None

class SessionInfo(BaseModel):
    session_id: str
    created_at: datetime
    message_count: int
    last_active: datetime

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, bool]

# Routes
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "TheraBot SaaS API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        services={
            "safety_module": safety_checker.is_healthy(),
            "memory_module": memory_manager.is_healthy(),
            "therapist_module": therapist_engine.is_healthy()
        }
    )

@app.post("/chat", response_model=ChatResponseModel, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint with full safety pipeline
    """
    try:
        # Generate or validate session
        if not request.session_id:
            session_id = str(uuid.uuid4())
        else:
            session_id = request.session_id
            
        # Get or create session
        session = memory_manager.get_or_create_session(
            session_id=session_id,
            user_id=request.user_id
        )
        
        # Step 1: Safety Analysis
        safety_result = safety_checker.analyze_message(request.message)
        
        # Step 2: Store user message in memory
        memory_manager.store_message(
            session_id=session_id,
            message=request.message,
            is_user=True,
            safety_metadata=safety_result.metadata
        )
        
        # Step 3: Check for crisis - immediate response if needed
        if safety_result.is_crisis:
            crisis_response = safety_checker.get_crisis_response(safety_result)
            
            # Store crisis response
            memory_manager.store_message(
                session_id=session_id,
                message=crisis_response.message,
                is_user=False,
                safety_metadata={"crisis_response": True}
            )
            
            return ChatResponseModel(
                message=crisis_response.message,
                session_id=session_id,
                timestamp=datetime.now(),
                is_crisis=True,
                safety_level="critical",
                crisis_resources=crisis_response.resources
            )
        
        # Step 4: Generate therapeutic response
        chat_history = memory_manager.get_session_history(session_id)
        therapist_response = therapist_engine.generate_response(
            user_message=request.message,
            safety_context=safety_result,
            chat_history=chat_history
        )
        
        # Step 5: Store bot response
        memory_manager.store_message(
            session_id=session_id,
            message=therapist_response.message,
            is_user=False,
            safety_metadata={"therapy_response": True}
        )
        
        # Update session
        memory_manager.update_session_activity(session_id)
        
        return ChatResponseModel(
            message=therapist_response.message,
            session_id=session_id,
            timestamp=datetime.now(),
            is_crisis=False,
            safety_level=safety_result.level,
            crisis_resources=None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing error: {str(e)}"
        )

@app.get("/sessions/{session_id}", tags=["Sessions"])
async def get_session_info(session_id: str):
    """Retrieve session information and history"""
    session = memory_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    history = memory_manager.get_session_history(session_id)
    
    return {
        "session": {
            "id": session.session_id,
            "created_at": session.created_at,
            "last_active": session.last_active,
            "message_count": session.message_count
        },
        "history": history
    }

@app.delete("/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """Delete a session and all associated data"""
    success = memory_manager.delete_session(session_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return {"message": "Session deleted successfully"}

@app.post("/safety/analyze", tags=["Safety"])
async def analyze_message(message: str):
    """Direct safety analysis endpoint"""
    result = safety_checker.analyze_message(message)
    return {
        "is_crisis": result.is_crisis,
        "level": result.level,
        "keywords": result.keywords,
        "confidence": result.confidence,
        "metadata": result.metadata
    }

# WebSocket endpoint for real-time chat
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # Process message through pipeline
            safety_result = safety_checker.analyze_message(message)
            
            if safety_result.is_crisis:
                crisis_response = safety_checker.get_crisis_response(safety_result)
                await websocket.send_json({
                    "type": "crisis_response",
                    "message": crisis_response.message,
                    "resources": crisis_response.resources
                })
            else:
                # Get chat history
                chat_history = memory_manager.get_session_history(session_id)
                
                # Generate response
                response = therapist_engine.generate_response(
                    user_message=message,
                    safety_context=safety_result,
                    chat_history=chat_history
                )
                
                await websocket.send_json({
                    "type": "response",
                    "message": response.message
                })
                
    except WebSocketDisconnect:
        print(f"Client disconnected: {session_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Error: {str(e)}"
        })

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
