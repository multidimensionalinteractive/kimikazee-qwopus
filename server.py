#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kimikazee Qwopus - FastAPI Server with OpenAI-compatible API

A production-ready FastAPI server for running Qwen3.5-9B-Uncensored models
via llama-cpp-python backend with SSE streaming support.

Features:
- Async/await for all I/O operations
- OpenAI-compatible /v1/chat/completions endpoint
- SSE streaming for real-time token generation
- Configurable parameters from config.yaml
- Health checks and graceful shutdown handling
- CORS middleware for cross-origin requests

Author: Kimikazee Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Union

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel, Field, validator

# llama-cpp-python imports
from llama_cpp import Llama, LlamaGrammar
from llama_cpp.llama_tokenizer import LlamaTokenizer

# Kimikazee prompt + temperature routing
from prompts.system_prompt import (
    build_system_prompt,
    detect_task_type,
    get_temperature,
    KIMIKAzee_SYSTEM_PROMPT,
)

# =============================================================================
# CONFIGURATION LOADING
# =============================================================================


def load_config(config_path: str = "config.yaml") -> Dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration settings
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is malformed
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Expand environment variables in config values
    for key, value in config.items():
        if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            config[key] = os.environ.get(env_var, value)
    
    return config


def setup_logging(config: Dict) -> logging.Logger:
    """
    Configure structured logging based on config settings.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured logger instance
    """
    log_level = config.get("log_level", "INFO")
    log_file = config.get("log_file", "~/.hermes-beta/logs/agent.log")
    
    # Expand home directory
    log_file = os.path.expanduser(log_file)
    
    # Create log directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    log_format = (
        "%(asctime)s | %(levelname)-8s | "
        "%(name)s:%(lineno)d | %(message)s"
    )
    
    # Create logger
    logger = logging.getLogger("qwopus.server")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # File handler for persistent logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(file_handler)
    
    return logger


# =============================================================================
# PYDANTIC MODELS - Request/Response Validation
# =============================================================================


class ChatMessage(BaseModel):
    """Represents a single chat message in the conversation."""
    role: str = Field(
        ..., 
        description="Role of the message sender",
        pattern="^(user|assistant|system|tool)$"
    )
    content: Union[str, List[Dict]] = Field(
        ...,
        description="Content of the message"
    )
    
    @validator('role')
    def validate_role(cls, v):
        """Validate that role is one of the allowed values."""
        allowed_roles = {"user", "assistant", "system", "tool"}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class ChatCompletionRequest(BaseModel):
    """
    OpenAI-compatible chat completion request model.
    
    Fields mirror the OpenAI API specification for maximum compatibility.
    """
    model: str = Field(
        "qwopus",
        description="Identifier of the model to use"
    )
    messages: List[ChatMessage] = Field(
        ...,
        min_items=1,
        description="List of conversation messages"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness in output generation"
    )
    top_p: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling: include top-p probability mass"
    )
    top_k: Optional[int] = Field(
        default=40,
        ge=1,
        le=100,
        description="Limit sampling to top-k tokens"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum number of tokens to generate (-1 for unlimited)"
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="Stop sequences where generation should halt"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="If true, return streaming response via SSE"
    )
    stream_options: Optional[Dict] = Field(
        default=None,
        description="Options for streaming response"
    )
    frequency_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalize repeated tokens"
    )
    presence_penalty: Optional[float] = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Penalize tokens based on frequency"
    )
    response_format: Optional[Dict] = Field(
        default=None,
        description="Response format specification (JSON mode)"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )
    logit_bias: Optional[Dict[str, float]] = Field(
        default=None,
        description="Logit bias for specific tokens"
    )
    user: Optional[str] = Field(
        default=None,
        description="End-user identifier for monitoring/auditing"
    )


class Choice(BaseModel):
    """Represents a single choice in the response."""
    index: int = Field(0, description="Index of this choice")
    message: ChatMessage = Field(
        ...,
        description="The assistant's response message"
    )
    finish_reason: Optional[str] = Field(
        None,
        description="Reason why generation finished",
        pattern="^(stop|length|tool_calls|content_filter|null)$"
    )
    logprobs: Optional[Dict] = Field(
        None,
        description="Token-level log probabilities (if enabled)"
    )


class ChatUsage(BaseModel):
    """Token usage statistics for the completion."""
    prompt_tokens: int = Field(0, description="Tokens in the prompt")
    completion_tokens: int = Field(0, description="Tokens generated")
    total_tokens: int = Field(0, description="Total tokens used")


class ChatCompletionResponse(BaseModel):
    """
    OpenAI-compatible chat completion response model.
    
    Provides structured response format matching OpenAI's API.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this completion"
    )
    choices: List[Choice] = Field(
        ...,
        description="List of response choices"
    )
    created: int = Field(
        ...,
        description="Unix timestamp of when completion was created"
    )
    model: str = Field(
        ...,
        description="Identifier of the model used"
    )
    object: str = Field(
        "chat.completion",
        description="Object type identifier"
    )
    usage: ChatUsage = Field(
        ...,
        description="Token usage statistics"
    )


class ChatCompletionStreamChoice(BaseModel):
    """Streaming version of Choice for SSE responses."""
    delta: ChatMessage = Field(
        ...,
        description="The message delta being streamed"
    )
    finish_reason: Optional[str] = Field(
        None,
        description="Reason why generation finished"
    )


class ChatCompletionStreamResponse(BaseModel):
    """Streaming response for SSE format."""
    id: str = Field(
        ...,
        description="Unique identifier for this completion"
    )
    choices: List[ChatCompletionStreamChoice] = Field(
        ...,
        description="List of streaming choices"
    )
    created: int = Field(
        ...,
        description="Unix timestamp"
    )
    model: str = Field(
        ...,
        description="Model identifier"
    )
    object: str = Field(
        "chat.completion.chunk",
        description="Object type for streaming"
    )


class ModelResponse(BaseModel):
    """Response for /v1/models endpoint."""
    id: str = Field(..., description="Model identifier")
    object: str = Field("model", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    owned_by: str = Field("qwopus", description="Model owner")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field("healthy", description="Server health status")
    model_loaded: bool = Field(..., description="Whether model is loaded")
    version: str = Field("1.0.0", description="Server version")


# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================


class AppState:
    """
    Manages global application state including the LLM instance.
    
    Thread-safe access to model and configuration.
    """
    def __init__(self, config: Dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.model: Optional[Llama] = None
        self.model_path: Optional[str] = None
        self.is_loaded = False
        self.startup_time: Optional[float] = None
    
    def load_model(self) -> None:
        """
        Load the LLM model from GGUF file.
        
        Uses llama-cpp-python for inference. Supports:
        - Flash attention optimization
        - GPU offloading
        - Parallel processing
        - Large context windows (128K)
        """
        self.logger.info("Initializing Kimikazee Qwopus server...")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
        
        try:
            # Get model path
            model_name = self.config.get("model", "Qwen3.5-9B-Uncensored-Q8_0.gguf")
            # Try multiple possible locations
            possible_paths = [
                model_name,  # Current directory
                os.path.join(os.path.dirname(__file__), model_name),
                os.path.expanduser(f"~/models/{model_name}"),
                os.path.expanduser(f"~/.cache/llama.cpp/{model_name}"),
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                self.logger.warning(f"Model file not found: {model_name}")
                self.logger.info("Model will be loaded lazily on first request")
                self.model_path = model_name
                return
            
            self.model_path = model_path
            self.logger.info(f"Loading model from: {model_path}")
            
            # Load configuration parameters
            context_window = self.config.get("context_window", 128000)
            n_threads = self.config.get("n_threads", 8)
            n_gpu_layers = self.config.get("n_gpu_layers", 0)
            flash_attn = self.config.get("flash_attn", True)
            parallel = self.config.get("parallel", 4)
            
            # Build llama-cpp-python parameters
            kwargs = {
                "model_path": model_path,
                "n_ctx": context_window,  # Context window size (128K max)
                "n_threads": n_threads,
                "n_gpu_layers": n_gpu_layers,
                "verbose": self.logger.level <= logging.DEBUG,
                "flash_attn": flash_attn,  # Enable flash attention if available
                "n_batch": min(context_window // 8, 2048),  # Batch size
                "n_parallel": parallel,  # Number of parallel sequences
                "embedding": True,  # Enable embeddings for context handling
                "mlock": True,  # Lock model in memory
                "memory_f32": False,  # Save VRAM
            }
            
            # Check if GPU is available and enable if requested
            if n_gpu_layers == -1:
                self.logger.info("GPU offload: ALL LAYERS")
                kwargs["n_gpu_layers"] = -1
            elif n_gpu_layers > 0:
                self.logger.info(f"GPU offload: {n_gpu_layers} layers")
            
            # Load model with context manager for better error handling
            self.logger.info("Loading model into memory... this may take a moment")
            self.model = Llama(**kwargs)
            self.is_loaded = True
            self.startup_time = time.time()
            
            self.logger.info(
                f"Model loaded successfully! "
                f"Context: {context_window}, Threads: {n_threads}, "
                f"GPU Layers: {n_gpu_layers}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self.logger.error(
                "The server will continue but will not be able to generate responses"
            )
            self.is_loaded = False
            raise
    
    def get_model(self) -> Llama:
        """Get the model instance, loading it lazily if needed."""
        if self.model is None and self.model_path:
            self.load_model()
        return self.model


# Global application state
app_state: Optional[AppState] = None
app: Optional[FastAPI] = None
shutdown_event = asyncio.Event()


# =============================================================================
# CONTEXT MANAGEMENT & PROMPT FORMATTING
# =============================================================================


def format_qwen_prompt(messages: List[Dict]) -> str:
    """
    Format conversation messages for Qwen model.
    
    Qwen uses a specific chat template with special tokens:
    - <|im_start|>user<|im_end|>
    - <|im_start|>assistant<|im_end|>
    - <|im_start|>system<|im_end|>
    
    Args:
        messages: List of message dictionaries with role and content
        
    Returns:
        Formatted prompt string ready for tokenization
    """
    if not messages:
        return ""
    
    # Build prompt using Qwen's chat template
    prompt = ""
    for i, msg in enumerate(messages):
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        # Handle system messages differently
        if role == "system":
            prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
        else:
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    
    # Assistant's turn
    prompt += "<|im_start|>assistant\n"
    
    return prompt


def apply_stop_sequences(
    generator, 
    stop_sequences: Optional[List[str]],
    max_tokens: Optional[int]
) -> str:
    """
    Apply stop sequences and token limits to a generator.
    
    Args:
        generator: The llama-cpp-python completion generator
        stop_sequences: List of stop sequences
        max_tokens: Maximum tokens to generate
        
    Returns:
        Complete generated text
    """
    generated_text = ""
    token_count = 0
    max_tokens = max_tokens if max_tokens is not None else -1
    
    for output in generator:
        token = output["choices"][0]["text"]
        generated_text += token
        token_count += 1
        
        # Check for stop sequences
        if stop_sequences:
            for stop in stop_sequences:
                if stop in generated_text:
                    # Remove stop sequence from output
                    generated_text = generated_text.replace(stop, "")
                    return generated_text
        
        # Check token limit
        if max_tokens > 0 and token_count >= max_tokens:
            return generated_text
    
    return generated_text


# =============================================================================
# SSE STREAMING HANDLERS
# =============================================================================


def encode_sse_message(data: Dict) -> str:
    """
    Encode a dictionary as an SSE (Server-Sent Event) message.
    
    SSE format requires:
    - Data prefixed with "data: "
    - Double newline at end
    
    Args:
        data: Dictionary to encode
        
    Returns:
        SSE-formatted string
    """
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def generate_stream_response(
    messages: List[Dict],
    request: ChatCompletionRequest
) -> AsyncGenerator[str, None]:
    """
    Generate streaming response using Server-Sent Events.
    
    For each token generated:
    1. Encode as SSE message
    2. Send to client with chunked encoding
    3. Track token statistics
    
    Args:
        messages: Conversation messages
        request: Original completion request
        
    Yields:
        SSE-formatted response chunks
    """
    model = app_state.get_model()
    
    if not app_state.is_loaded:
        error_msg = encode_sse_message({
            "error": {
                "type": "service_unavailable",
                "message": "Model not loaded",
                "code": 503
            }
        })
        yield error_msg
        return
    
    # Format the prompt
    prompt = format_qwen_prompt(messages)
    
    # Get generation parameters from request or config
    msg_dicts = [m if isinstance(m, dict) else m.model_dump() for m in messages]
    task_type = detect_task_type(msg_dicts)
    default_temp = get_temperature(task_type)
    temperature = request.temperature if request.temperature is not None else default_temp
    top_p = request.top_p or app_state.config.get("top_p", 0.9)
    top_k = request.top_k or app_state.config.get("top_k", 40)
    max_tokens = request.max_tokens or app_state.config.get("n_predict", -1)
    stop = request.stop or None

    # Inject system prompt if none present
    has_system = any(
        (m.get("role") if isinstance(m, dict) else getattr(m, "role", None)) == "system"
        for m in messages
    )
    if not has_system:
        messages.insert(0, {"role": "system", "content": KIMIKAzee_SYSTEM_PROMPT})
    
    # Generate with streaming
    stream = model.create_chat_completion(
        messages=messages,
        temperature=temperature,
        top_p=top_p,
        top_k=top_k,
        max_tokens=max_tokens,
        stop=stop,
        stream=True,
    )
    
    # Stream tokens to client
    completion_id = str(uuid.uuid4())
    created = int(time.time())
    choice_id = 0
    
    for chunk in stream:
        choice = chunk.get("choices", [{}])[0]
        delta = choice.get("delta", {})
        finish_reason = choice.get("finish_reason")
        
        # Create streaming response object
        response = ChatCompletionStreamResponse(
            id=completion_id,
            model=request.model or "qwopus",
            created=created,
            object="chat.completion.chunk",
            choices=[
                ChatCompletionStreamChoice(
                    index=choice_id,
                    delta=ChatMessage(
                        role="assistant",
                        content=delta.get("content", "")
                    ),
                    finish_reason=finish_reason
                )
            ]
        )
        
        yield encode_sse_message(response.model_dump(exclude_none=True))
        
        if finish_reason:
            break
    
    # Send final event
    final_response = encode_sse_message({
        "choices": [
            {
                "finish_reason": "stop",
                "index": 0
            }
        ],
        "id": completion_id,
        "model": request.model or "qwopus",
        "created": created,
        "object": "chat.completion.chunk"
    })
    yield final_response


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.
    
    Handles:
    - Model loading on startup
    - Graceful shutdown on SIGINT/SIGTERM
    """
    global app_state
    
    # Startup
    logger = app_state.logger
    logger.info("=" * 60)
    logger.info("Kimikazee Qwopus Server Starting Up")
    logger.info("=" * 60)
    
    try:
        app_state.load_model()
    except Exception as e:
        logger.error(f"Model loading error: {e}")
        logger.warning("Server will start but model-dependent endpoints will fail")
    
    logger.info(f"Server ready on port {8080}")
    logger.info(f"API endpoints:")
    logger.info(f"  - GET  /health")
    logger.info(f"  - GET  /v1/models")
    logger.info(f"  - POST /v1/chat/completions")
    logger.info("=" * 60)
    
    yield
    
    # Shutdown
    logger.info("Shutting down Kimikazee Qwopus...")
    
    if app_state.model:
        del app_state.model
        app_state.model = None
        app_state.is_loaded = False
    
    logger.info("Server shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Configures:
    - Middleware (CORS)
    - Lifespan events
    - Routes and handlers
    - Exception handlers
    
    Returns:
        Configured FastAPI instance
    """
    global app, app_state
    
    # Load configuration
    config_path = os.environ.get("QWOPUS_CONFIG", "config.yaml")
    config = load_config(config_path)
    
    # Setup logging
    logger = setup_logging(config)
    
    # Initialize global state
    app_state = AppState(config, logger)
    
    # Create FastAPI app
    app = FastAPI(
        title="Kimikazee Qwopus API",
        description=(
            "A production-ready API server for running Qwen3.5-9B-Uncensored "
            "models via llama-cpp-python. Provides OpenAI-compatible endpoints "
            "with SSE streaming support."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # =================================================================
    # ROUTE HANDLERS
    # =================================================================
    
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """
        Health check endpoint.
        
        Returns the server's health status and model availability.
        
        Returns:
            HealthResponse with status information
        """
        return HealthResponse(
            status="healthy" if app_state.is_loaded else "degraded",
            model_loaded=app_state.is_loaded,
            version="1.0.0"
        )
    
    @app.get("/v1/models", response_model=List[ModelResponse], tags=["Models"])
    async def list_models():
        """
        List available models.
        
        Returns the models available for chat completions.
        
        Returns:
            List of ModelResponse objects
        """
        model_name = app_state.config.get("model", "qwopus")
        return [
            ModelResponse(
                id=model_name,
                object="model",
                created=int(time.time()),
                owned_by="qwopus"
            )
        ]
    
    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse, tags=["Chat"])
    async def chat_completions(
        request: ChatCompletionRequest,
        raw_request: Request
    ):
        """
        Main chat completion endpoint.
        
        OpenAI-compatible endpoint that accepts chat messages and returns
        AI-generated responses. Supports both regular and streaming modes.
        
        Args:
            request: ChatCompletionRequest with messages and parameters
            raw_request: Raw HTTP request for streaming detection
            
        Returns:
            ChatCompletionResponse with model's completion
            
        Raises:
            HTTPException: If model is not loaded or request is invalid
        """
        # Check if streaming is requested
        is_streaming = request.stream or (
            hasattr(raw_request, "headers") and 
            "accept" in dict(raw_request.headers) and 
            "text/event-stream" in dict(raw_request.headers)["accept"]
        )
        
        if is_streaming:
            # Return streaming response
            return StreamingResponse(
                generate_stream_response(request.messages, request),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                }
            )
        
        # Non-streaming response
        model = app_state.get_model()
        
        if not app_state.is_loaded:
            raise HTTPException(
                status_code=503,
                detail="Model not loaded. Server is starting up."
            )
        
        # Get generation parameters
        # Smart temperature routing: detect task type, override if caller didn't specify
        task_type = detect_task_type([m.model_dump() for m in request.messages])
        default_temp = get_temperature(task_type)
        temperature = request.temperature if request.temperature is not None else default_temp
        top_p = request.top_p or app_state.config.get("top_p", 0.9)
        top_k = request.top_k or app_state.config.get("top_k", 40)
        max_tokens = request.max_tokens or app_state.config.get("n_predict", -1)
        stop = request.stop or None

        # Inject anti-hallucination system prompt if no system message present
        messages = list(request.messages)
        has_system = any(m.role == "system" for m in messages)
        if not has_system:
            sys_msg = ChatMessage(role="system", content=KIMIKAzee_SYSTEM_PROMPT)
            messages.insert(0, sys_msg)

        # Add repeat_penalty + min_p from config
        repeat_penalty = app_state.config.get("repeat_penalty", 1.1)
        repeat_penalty_last_n = app_state.config.get("repeat_penalty_last_n", 256)
        
        # Format prompt and generate
        prompt = format_qwen_prompt([m.model_dump() for m in messages])
        
        try:
            # Generate completion
            start_time = time.time()
            
            result = model.create_chat_completion(
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                max_tokens=max_tokens,
                stop=stop,
                stream=False,
                repeat_penalty=repeat_penalty,
            )
            
            generation_time = time.time() - start_time
            
            # Extract response
            completion = result["choices"][0]["message"]["content"]
            finish_reason = result["choices"][0].get("finish_reason", "stop")
            
            # Count tokens
            prompt_tokens = len(model.tokenize(prompt.encode()))
            completion_tokens = len(model.tokenize(completion.encode()))
            
            return ChatCompletionResponse(
                id=str(uuid.uuid4()),
                choices=[
                    Choice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=completion
                        ),
                        finish_reason=finish_reason
                    )
                ],
                created=int(time.time()),
                model=request.model or "qwopus",
                object="chat.completion",
                usage=ChatUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens
                )
            )
            
        except Exception as e:
            app_state.logger.error(f"Generation error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Generation failed: {str(e)}"
            )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """
        Global exception handler for unhandled errors.
        
        Returns a user-friendly error response.
        """
        app_state.logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": str(exc),
                    "code": 500
                }
            }
        )
    
    return app


# =============================================================================
# GRACEFUL SHUTDOWN HANDLER
# =============================================================================


def setup_signal_handlers(app: FastAPI):
    """
    Set up signal handlers for graceful shutdown.
    
    Handles SIGINT (Ctrl+C) and SIGTERM for clean shutdown.
    """
    def shutdown_handler(signum, frame):
        """Handle shutdown signals."""
        app_state.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    """
    Main entry point for the server.
    
    Starts the FastAPI server using uvicorn with:
    - 8 workers for production
    - 0.0.0.0 to accept external connections
    - Graceful shutdown handling
    """
    global app
    
    # Create the application
    app = create_app()
    
    # Set up signal handlers
    setup_signal_handlers(app)
    
    # Get server configuration
    port = int(os.environ.get("QWOPUS_PORT", "8080"))
    host = os.environ.get("QWOPUS_HOST", "0.0.0.0")
    
    # Determine host - use 0.0.0.0 if listening externally
    if os.environ.get("QWOPUS_EXTERNAL", "").lower() in ("true", "1", "yes"):
        host = "0.0.0.0"
    
    # Start server
    import uvicorn
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        workers=1,  # Single worker for single-GPU models
        reload=False,  # Disable auto-reload in production
        log_level="info",
        access_log=True,
        http="httptools",  # Faster HTTP parser
    )


# =============================================================================
# UNIT TESTS & VALIDATION
# =============================================================================


def test_config_loading():
    """Test configuration loading with various scenarios."""
    import tempfile
    
    # Test 1: Valid config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("test: value\n")
        config_path = f.name
    
    try:
        config = load_config(config_path)
        assert config["test"] == "value"
        print("✓ Config loading test passed")
    finally:
        os.unlink(config_path)


def test_pydantic_models():
    """Test Pydantic model validation."""
    # Test ChatMessage
    msg = ChatMessage(role="user", content="Hello")
    assert msg.role == "user"
    assert msg.content == "Hello"
    
    # Test invalid role
    try:
        ChatMessage(role="invalid", content="test")
        assert False, "Should have raised ValidationError"
    except Exception:
        pass  # Expected
    
    # Test ChatCompletionRequest
    request = ChatCompletionRequest(
        model="test",
        messages=[ChatMessage(role="user", content="Hi")]
    )
    assert request.model == "test"
    
    print("✓ Pydantic models test passed")


def test_prompt_formatting():
    """Test Qwen prompt formatting."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
    ]
    
    prompt = format_qwen_prompt(messages)
    assert "<|im_start|>system" in prompt
    assert "<|im_start|>user" in prompt
    assert "<|im_start|>assistant" in prompt
    
    print("✓ Prompt formatting test passed")


if __name__ == "__main__":
    # Run tests if module is executed directly
    print("Running unit tests...")
    test_config_loading()
    test_pydantic_models()
    test_prompt_formatting()
    print("\nAll tests passed! ✓")
    
    # Start server
    main()
