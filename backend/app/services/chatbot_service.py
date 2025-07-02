from app.chatbot.chat_engine import ChatEngine
from app.schema.chat_schema import MessageResponse
from app.services.base_service import BaseService


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
                        # Clean chunk from error prefixes if they exist
                        if not chunk.startswith("ERROR:"):
                            full_response += chunk
                            yield chunk
                        else:
                            # Pass error messages through but don't save them
                            yield chunk
                            return
            except Exception as e:
                error_msg = f"ERROR: Failed to generate response - {str(e)}"
                print(error_msg)
                yield error_msg
                return

        except Exception as e:
            error_msg = f"ERROR: {str(e)}"
            print(error_msg)
            yield error_msg



