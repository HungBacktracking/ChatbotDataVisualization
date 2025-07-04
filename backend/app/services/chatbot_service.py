from app.chatbot.chat_engine import ChatEngine
from app.schema.chat_schema import MessageResponse
from app.services.base_service import BaseService
import json


# Helper function to adapt different types of generators to async generator
async def async_generator_adapter(generator):
    """
    Adapts any type of generator (sync or async) to be used with async for.
    """
    # If it's already an async generator
    if hasattr(generator, '__aiter__'):
        try:
            async for item in generator:
                yield item
        except Exception as e:
            print(f"Error in async generator: {e}")
            raise
    else:
        # If it's a regular generator or iterable
        try:
            if hasattr(generator, '__iter__'):
                for item in generator:
                    yield item
            else:
                # If it's not iterable at all, yield it as a single item
                yield generator
        except TypeError:
            # If it's not iterable at all, yield it as a single item
            yield generator
        except Exception as e:
            print(f"Error in sync generator: {e}")
            raise


class ChatbotService(BaseService):
    def __init__(
            self,
            chat_engine: ChatEngine
    ):
        self.chat_engine = chat_engine
        super().__init__()

    async def generate_message_stream(self, session_id: str, message: str, history: list[MessageResponse]):
        try:

            history = history or []
            history = [message.model_dump() for message in history]
            self.chat_engine.compose(session_id, history, message)

            full_response = ""
            try:
                generator = self.chat_engine.stream_chat(message)
                if hasattr(generator, '__await__'):
                    generator = await generator

                async for chunk in async_generator_adapter(generator):
                    if chunk:
                        # Handle error messages
                        if chunk.startswith("ERROR:"):
                            yield chunk
                            return

                        # Try to parse as JSON
                        try:
                            data = json.loads(chunk)

                            # Handle text chunks
                            if data.get("type") == "text":
                                content = data.get("content", "")
                                full_response += content
                                yield content

                            # Handle chart data
                            elif data.get("type") == "chart":
                                # Yield chart data as special format
                                chart_json = json.dumps(data, ensure_ascii=False)
                                yield f"CHART:{chart_json}"

                        except json.JSONDecodeError:
                            # If it's not JSON, treat as text (backward compatibility)
                            full_response += chunk
                            yield chunk

            except Exception as e:
                error_msg = f"ERROR: Failed to generate response - {str(e)}"
                print(error_msg)
                yield error_msg
                return

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(error_msg)
            yield error_msg



