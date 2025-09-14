"""OpenAI Chat Completions API endpoint."""

from fastapi import APIRouter, HTTPException, Request

from motive_proxy.session_manager import SessionManager
from motive_proxy.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ErrorResponse,
    ErrorDetails,
)
from motive_proxy.observability import get_logger, extract_request_context, generate_correlation_id, time_operation

router = APIRouter()

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
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
    request_context.update({
        "correlation_id": correlation_id,
        "session_id": request.model,
        "message_count": len(request.messages),
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

    # Route through the session layer implementing handshake/turn protocol
    session_manager: SessionManager = fastapi_request.app.state.session_manager
    
    with time_operation("session_processing", {"session_id": request.model}):
        session = await session_manager.get_or_create(request.model)
        
        try:
            counterpart_message = await session.process_request(content)
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
        model=request.model, prompt=content, completion=counterpart_message
    )
    
    logger.info("Chat completion response sent", 
               **request_context,
               response_id=response.id)
    
    return response
