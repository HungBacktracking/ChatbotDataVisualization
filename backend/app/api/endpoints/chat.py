from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.containers.application_container import ApplicationContainer

from app.schema.chat_schema import MessageResponse, MessageCreate
from app.services.chatbot_service import ChatbotService

router = APIRouter(prefix="/chat", tags=["Chatbot"])



@router.post("/generate-response")
@inject
async def generate_response(
    session_id: str,
    data: MessageCreate,
    service: ChatbotService = Depends(Provide[ApplicationContainer.services.chatbot_service])
):
    async def response_generator():
        try:
            yield "event: start\ndata: \n\n"
            
            async for chunk in service.generate_message_stream(session_id, data.content):
                if chunk:
                    # Handle error messages with ERROR: prefix
                    if chunk.startswith("ERROR:"):
                        error_message = chunk[6:].strip()  # Remove the ERROR: prefix and trim whitespace
                        yield f"event: error\ndata: {error_message}\n\n"
                        return
                        
                    if not isinstance(chunk, str):
                        chunk = str(chunk)

                    formatted_chunk = chunk.replace("\n", "\\n")
                    yield f"event: message\ndata: {formatted_chunk}\n\n"

            yield "event: done\ndata: \n\n"
            
        except Exception as e:
            error_message = str(e)
            yield f"event: error\ndata: {error_message}\n\n"
            
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in Nginx
        }
    )





