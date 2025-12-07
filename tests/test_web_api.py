"""
EVO-TR Web API Tests

Tests for FastAPI backend endpoints.
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWebAppStructure:
    """Test web app structure."""
    
    def test_app_module_exists(self):
        """App module should exist."""
        app_path = Path("src/web/app.py")
        assert app_path.exists(), "src/web/app.py should exist"
    
    def test_static_dir_exists(self):
        """Static directory should exist."""
        static_path = Path("src/web/static")
        assert static_path.exists(), "src/web/static should exist"
    
    def test_index_html_exists(self):
        """Index.html should exist."""
        index_path = Path("src/web/static/index.html")
        assert index_path.exists(), "src/web/static/index.html should exist"
    
    def test_run_server_exists(self):
        """Run server script should exist."""
        script_path = Path("scripts/run_server.py")
        assert script_path.exists(), "scripts/run_server.py should exist"


class TestAppImports:
    """Test app can be imported."""
    
    def test_import_fastapi(self):
        """FastAPI should be importable."""
        import fastapi
        assert fastapi is not None
    
    def test_import_app_module(self):
        """App module should be importable."""
        from src.web import app
        assert app is not None
    
    def test_app_instance_exists(self):
        """App instance should exist."""
        from src.web.app import app
        assert app is not None
    
    def test_app_has_routes(self):
        """App should have routes."""
        from src.web.app import app
        routes = [r.path for r in app.routes]
        assert len(routes) > 0


class TestEndpoints:
    """Test endpoint definitions."""
    
    def test_health_endpoint_exists(self):
        """Health endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/health" in routes
    
    def test_status_endpoint_exists(self):
        """Status endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/status" in routes
    
    def test_adapters_endpoint_exists(self):
        """Adapters endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/adapters" in routes
    
    def test_intents_endpoint_exists(self):
        """Intents endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/intents" in routes
    
    def test_route_endpoint_exists(self):
        """Route endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/route" in routes
    
    def test_chat_endpoint_exists(self):
        """Chat endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/chat" in routes
    
    def test_chat_stream_endpoint_exists(self):
        """Chat stream endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/chat/stream" in routes
    
    def test_websocket_endpoint_exists(self):
        """WebSocket endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/ws/chat" in routes


class TestPydanticModels:
    """Test Pydantic models."""
    
    def test_chat_request_model(self):
        """ChatRequest model should work."""
        from src.web.app import ChatRequest
        request = ChatRequest(message="Test")
        assert request.message == "Test"
        assert request.adapter is None
        assert request.stream is False
    
    def test_chat_response_model(self):
        """ChatResponse model should work."""
        from src.web.app import ChatResponse
        response = ChatResponse(
            response="Hello",
            intent="general_chat",
            adapter_used="base_model",
            confidence=0.95,
            tokens_generated=10,
            generation_time=1.5
        )
        assert response.response == "Hello"
        assert response.intent == "general_chat"
    
    def test_adapter_info_model(self):
        """AdapterInfo model should work."""
        from src.web.app import AdapterInfo
        info = AdapterInfo(
            name="test_adapter",
            path="/path/to/adapter",
            intent="test",
            description="Test adapter",
            size_mb=10.5,
            loaded=False
        )
        assert info.name == "test_adapter"
        assert info.size_mb == 10.5


class TestAppState:
    """Test AppState class."""
    
    def test_app_state_exists(self):
        """AppState should exist."""
        from src.web.app import AppState
        assert AppState is not None
    
    def test_app_state_init(self):
        """AppState should initialize."""
        from src.web.app import AppState
        state = AppState()
        assert state.orchestrator is None
        assert state.model_loaded is False
    
    def test_app_state_uptime(self):
        """AppState should track uptime."""
        from src.web.app import AppState
        import time
        state = AppState()
        time.sleep(0.1)
        uptime = state.get_uptime()
        assert uptime >= 0.1


class TestFrontendContent:
    """Test frontend HTML content."""
    
    def test_html_has_title(self):
        """HTML should have title."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "<title>EVO-TR" in content
    
    def test_html_has_chat_area(self):
        """HTML should have chat area."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "chat-area" in content
    
    def test_html_has_messages_container(self):
        """HTML should have messages container."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert 'id="messages"' in content
    
    def test_html_has_input(self):
        """HTML should have input field."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert 'id="messageInput"' in content
    
    def test_html_has_send_button(self):
        """HTML should have send button."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert 'id="sendButton"' in content
    
    def test_html_has_adapter_list(self):
        """HTML should have adapter list."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert 'id="adapterList"' in content
    
    def test_html_has_websocket_toggle(self):
        """HTML should have WebSocket toggle."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert 'id="wsToggle"' in content
    
    def test_html_has_streaming_functions(self):
        """HTML should have streaming functions."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "sendMessageViaSSE" in content
        assert "sendMessageViaWebSocket" in content
    
    def test_html_has_typing_cursor(self):
        """HTML should have typing cursor style."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "typing-cursor" in content
    
    def test_html_has_feedback_buttons_css(self):
        """HTML should have feedback button styles."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "feedback-btn" in content
        assert "thumbs-up" in content
        assert "thumbs-down" in content
    
    def test_html_has_feedback_function(self):
        """HTML should have sendFeedback function."""
        index_path = Path("src/web/static/index.html")
        content = index_path.read_text()
        assert "sendFeedback" in content
        assert "messageHistory" in content


class TestStreamingInfrastructure:
    """Test streaming infrastructure."""
    
    def test_mlx_inference_has_stream_generate(self):
        """MLXInference should have stream_generate."""
        from src.inference.mlx_inference import MLXInference
        inference = MLXInference()
        assert hasattr(inference, 'generate_stream')
    
    def test_mlx_inference_has_generate_response_stream(self):
        """MLXInference should have generate_response_stream."""
        from src.inference.mlx_inference import MLXInference
        inference = MLXInference()
        assert hasattr(inference, 'generate_response_stream')
    
    def test_orchestrator_has_chat_stream(self):
        """EvoTR should have chat_stream method."""
        from src.orchestrator import EvoTR
        assert hasattr(EvoTR, 'chat_stream')


class TestCORSConfig:
    """Test CORS configuration."""
    
    def test_cors_middleware_added(self):
        """CORS middleware should be added."""
        from src.web.app import app
        middleware_classes = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes


class TestFeedbackAPI:
    """Test feedback API endpoints."""
    
    def test_feedback_request_model_exists(self):
        """FeedbackRequest model should exist."""
        from src.web.app import FeedbackRequest
        assert FeedbackRequest is not None
    
    def test_feedback_response_model_exists(self):
        """FeedbackResponse model should exist."""
        from src.web.app import FeedbackResponse
        assert FeedbackResponse is not None
    
    def test_feedback_request_has_required_fields(self):
        """FeedbackRequest should have required fields."""
        from src.web.app import FeedbackRequest
        fields = FeedbackRequest.model_fields
        assert 'message_id' in fields
        assert 'user_message' in fields
        assert 'assistant_response' in fields
        assert 'feedback_type' in fields
    
    def test_feedback_request_has_optional_correction(self):
        """FeedbackRequest should have optional corrected_response field."""
        from src.web.app import FeedbackRequest
        fields = FeedbackRequest.model_fields
        assert 'corrected_response' in fields
        # Check if corrected_response is optional (has default)
        assert not fields['corrected_response'].is_required()
    
    def test_feedback_response_has_fields(self):
        """FeedbackResponse should have required fields."""
        from src.web.app import FeedbackResponse
        fields = FeedbackResponse.model_fields
        assert 'success' in fields
        assert 'feedback_id' in fields
        assert 'message' in fields
    
    def test_feedback_add_endpoint_exists(self):
        """POST /feedback/add endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/feedback/add" in routes
    
    def test_feedback_stats_endpoint_exists(self):
        """GET /feedback/stats endpoint should exist."""
        from src.web.app import app
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/feedback/stats" in routes
    
    def test_feedback_add_is_post(self):
        """POST /feedback/add should be POST method."""
        from src.web.app import app
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/feedback/add":
                assert "POST" in route.methods
    
    def test_feedback_stats_is_get(self):
        """GET /feedback/stats should be GET method."""
        from src.web.app import app
        for route in app.routes:
            if hasattr(route, 'path') and route.path == "/feedback/stats":
                assert "GET" in route.methods


class TestFeedbackDatabase:
    """Test feedback database functionality."""
    
    def test_feedback_database_module_exists(self):
        """Feedback database module should exist."""
        from src.lifecycle.feedback import FeedbackDatabase
        assert FeedbackDatabase is not None
    
    def test_feedback_record_dataclass_exists(self):
        """FeedbackEntry dataclass should exist."""
        from src.lifecycle.feedback import FeedbackEntry
        assert FeedbackEntry is not None
    
    def test_feedback_database_has_add_method(self):
        """FeedbackDatabase should have add_feedback method."""
        from src.lifecycle.feedback import FeedbackDatabase
        assert hasattr(FeedbackDatabase, 'add_feedback')
    
    def test_feedback_database_has_stats_method(self):
        """FeedbackDatabase should have get_stats method."""
        from src.lifecycle.feedback import FeedbackDatabase
        assert hasattr(FeedbackDatabase, 'get_stats')
    
    def test_feedback_database_has_get_feedback_method(self):
        """FeedbackDatabase should have get_feedback method."""
        from src.lifecycle.feedback import FeedbackDatabase
        assert hasattr(FeedbackDatabase, 'get_feedback')
    
    def test_feedback_database_has_session_feedback_method(self):
        """FeedbackDatabase should have get_session_feedback method."""
        from src.lifecycle.feedback import FeedbackDatabase
        assert hasattr(FeedbackDatabase, 'get_session_feedback')
    
    def test_feedback_database_creates_file(self):
        """FeedbackDatabase should create database file."""
        from src.lifecycle.feedback import FeedbackDatabase
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_feedback.db")
            db = FeedbackDatabase(db_path)
            assert os.path.exists(db_path)
    
    def test_feedback_database_add_returns_id(self):
        """add_feedback should return feedback ID."""
        from src.lifecycle.feedback import FeedbackDatabase, FeedbackEntry
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_feedback.db")
            db = FeedbackDatabase(db_path)
            
            entry = FeedbackEntry(
                session_id="test_session",
                message_id="test_message",
                user_message="test input",
                assistant_response="test response",
                adapter_used="test_adapter",
                feedback_type="thumbs_up"
            )
            feedback_id = db.add_feedback(entry)
            assert isinstance(feedback_id, str)
            assert len(feedback_id) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
