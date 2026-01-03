"""
User Memory and Session Management Module
"""
import json
import redis
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class ChatMessage:
    id: str
    session_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )

@dataclass
class UserSession:
    session_id: str
    user_id: Optional[str]
    created_at: datetime
    last_active: datetime
    message_count: int
    settings: Dict[str, Any]
    
    def update_activity(self):
        self.last_active = datetime.now()
        self.message_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "message_count": self.message_count,
            "settings": self.settings
        }

class MemoryManager:
    """Manages user sessions and chat history"""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379):
        """
        Initialize memory manager with Redis backend
        """
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print("✓ Connected to Redis")
        except redis.ConnectionError:
            print("⚠️ Redis not available, using in-memory storage")
            self.redis_client = None
            self._in_memory_store = {
                "sessions": {},
                "messages": {}
            }
    
    def get_or_create_session(self, session_id: str, user_id: Optional[str] = None) -> UserSession:
        """
        Retrieve existing session or create new one
        """
        session = self.get_session(session_id)
        
        if not session:
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now(),
                last_active=datetime.now(),
                message_count=0,
                settings={
                    "language": "ar",
                    "therapy_style": "supportive",
                    "safety_level": "standard",
                    "privacy_mode": True
                }
            )
            self._save_session(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Retrieve session by ID
        """
        if self.redis_client:
            session_data = self.redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                return UserSession(
                    session_id=data["session_id"],
                    user_id=data["user_id"],
                    created_at=datetime.fromisoformat(data["created_at"]),
                    last_active=datetime.fromisoformat(data["last_active"]),
                    message_count=data["message_count"],
                    settings=data["settings"]
                )
        else:
            return self._in_memory_store["sessions"].get(session_id)
        
        return None
    
    def _save_session(self, session: UserSession):
        """
        Save session to storage
        """
        if self.redis_client:
            session_data = json.dumps(session.to_dict())
            self.redis_client.setex(
                f"session:{session.session_id}",
                timedelta(hours=24),  # Session expires after 24 hours of inactivity
                session_data
            )
        else:
            self._in_memory_store["sessions"][session.session_id] = session
    
    def store_message(self, session_id: str, message: str, is_user: bool, 
                     safety_metadata: Optional[Dict] = None) -> str:
        """
        Store a chat message
        """
        message_id = str(uuid.uuid4())
        
        chat_message = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=MessageRole.USER if is_user else MessageRole.ASSISTANT,
            content=message,
            timestamp=datetime.now(),
            metadata=safety_metadata or {}
        )
        
        # Store message
        if self.redis_client:
            # Store in Redis list
            message_data = json.dumps(chat_message.to_dict())
            self.redis_client.lpush(f"messages:{session_id}", message_data)
            
            # Keep only last 100 messages per session
            self.redis_client.ltrim(f"messages:{session_id}", 0, 99)
        else:
            if session_id not in self._in_memory_store["messages"]:
                self._in_memory_store["messages"][session_id] = []
            self._in_memory_store["messages"][session_id].insert(0, chat_message)
            
            # Keep only last 100 messages
            self._in_memory_store["messages"][session_id] = \
                self._in_memory_store["messages"][session_id][:100]
        
        # Update session activity
        session = self.get_session(session_id)
        if session:
            session.update_activity()
            self._save_session(session)
        
        return message_id
    
    def get_session_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve chat history for a session
        """
        messages = []
        
        if self.redis_client:
            # Get from Redis
            message_data_list = self.redis_client.lrange(f"messages:{session_id}", 0, limit - 1)
            for message_data in message_data_list:
                try:
                    data = json.loads(message_data)
                    messages.append(data)
                except json.JSONDecodeError:
                    continue
        else:
            # Get from in-memory store
            session_messages = self._in_memory_store["messages"].get(session_id, [])
            for message in session_messages[:limit]:
                messages.append(message.to_dict())
        
        # Return in chronological order (oldest first)
        return sorted(messages, key=lambda x: x["timestamp"])
    
    def update_session_activity(self, session_id: str):
        """
        Update session last active timestamp
        """
        session = self.get_session(session_id)
        if session:
            session.last_active = datetime.now()
            self._save_session(session)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete session and all associated messages
        """
        try:
            if self.redis_client:
                # Delete session and messages
                self.redis_client.delete(f"session:{session_id}")
                self.redis_client.delete(f"messages:{session_id}")
            else:
                self._in_memory_store["sessions"].pop(session_id, None)
                self._in_memory_store["messages"].pop(session_id, None)
            
            return True
        except Exception:
            return False
    
    def cleanup_old_sessions(self, hours: int = 24):
        """
        Clean up sessions inactive for specified hours
        """
        # In production, implement Redis key expiration or scheduled cleanup
        pass
    
    def is_healthy(self) -> bool:
        """
        Health check for memory module
        """
        try:
            if self.redis_client:
                return self.redis_client.ping()
            return True  # In-memory storage is always "healthy"
        except:
            return False
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get memory module statistics
        """
        if self.redis_client:
            try:
                # Get Redis info
                info = self.redis_client.info()
                return {
                    "storage_type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "total_keys": self.redis_client.dbsize()
                }
            except:
                return {"storage_type": "redis", "status": "error"}
        else:
            return {
                "storage_type": "in_memory",
                "session_count": len(self._in_memory_store["sessions"]),
                "total_messages": sum(len(msgs) for msgs in self._in_memory_store["messages"].values())
            }
