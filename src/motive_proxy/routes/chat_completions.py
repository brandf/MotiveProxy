"""OpenAI Chat Completions API endpoint."""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from motive_proxy.session_manager import SessionManager
from motive_proxy.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorResponse,
    ErrorDetails,
)
from motive_proxy.observability import get_logger, extract_request_context, generate_correlation_id, time_operation
from motive_proxy.streaming import StreamingSession

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, fastapi_request: Request):
    """
    OpenAI Chat Completions API endpoint.

    This endpoint handles the proxy logic for human-in-the-loop interactions.
    """
    # Generate correlation ID for request tracing
    correlation_id = generate_correlation_id()
    logger = get_logger("motive_proxy.chat_completions")
    
    # Extract request context for logging
    request_context = extract_request_context(fastapi_request)
    # Support model format "<session_id>|<side>" so clients can identify side explicitly
    raw_model = request.model
    session_id = raw_model
    sender_side = None
    if isinstance(raw_model, str) and "|" in raw_model:
        try:
            session_id, side_str = raw_model.split("|", 1)
            from motive_proxy.session import Side
            sender_side = Side(side_str) if side_str in ("A", "B") else None
        except Exception:
            session_id = raw_model
            sender_side = None

    request_context.update({
        "correlation_id": correlation_id,
        "session_id": session_id,
        "message_count": len(request.messages),
        "sender_side": str(sender_side) if sender_side else None,
    })
    
    logger.info("Chat completion request received", **request_context)
    
    # Basic validation - check for empty messages
    if not request.messages:
        logger.warning("Empty messages array received", **request_context)
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error=ErrorDetails(
                    message="Messages array cannot be empty",
                    type="invalid_request_error",
                    code="messages_empty",
                )
            ).model_dump()
        )

    # Extract the last user message content as the request payload
    content = request.messages[-1].content
    request_context["message_content_length"] = len(content)
    request_context["stream"] = getattr(request, 'stream', False)

    # Route through the session layer implementing handshake/turn protocol
    session_manager: SessionManager = fastapi_request.app.state.session_manager
    
    # Check if streaming is requested
    if getattr(request, 'stream', False):
        logger.info("Streaming request detected", **request_context)
        
        async def generate_stream():
            streaming_session = StreamingSession(session_id, session_id)
            session = await session_manager.get_or_create(session_id)
            
            async for chunk in streaming_session.process_streaming_request(content, session):
                yield chunk
            
            # Send final SSE terminator
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
            }
        )
    
    # Non-streaming response (existing logic)
    with time_operation("session_processing", {"session_id": session_id}):
        session = await session_manager.get_or_create(session_id)
        
        try:
            counterpart_message = await session.process_request(content, sender_side=sender_side)
            logger.info("Message processed successfully", 
                       **request_context,
                       response_length=len(counterpart_message))
        except TimeoutError:
            logger.warning("Request timed out", **request_context)
            raise HTTPException(
                status_code=408,
                detail=ErrorResponse(
                    error=ErrorDetails(
                        message="Request timed out",
                        type="timeout_error",
                        code="timeout",
                    )
                ).model_dump(),
            )
        except Exception as exc:  # pragma: no cover (safety net)
            logger.error("Unexpected error processing request", 
                        **request_context,
                        error=str(exc),
                        exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error=ErrorDetails(
                        message=str(exc),
                        type="server_error",
                        code="internal_error",
                    )
                ).model_dump(),
            )

    response = ChatCompletionResponse.build(
        model=session_id, prompt=content, completion=counterpart_message
    )
    
    logger.info("Chat completion response sent", 
               **request_context,
               response_id=response.id)
    
    return response
