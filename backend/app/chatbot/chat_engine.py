
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.chat_engine import (
    CondensePlusContextChatEngine
)

import nest_asyncio
import json
import asyncio

nest_asyncio.apply()

import logging

# Bật logging toàn cục mức INFO
logging.basicConfig(level=logging.DEBUG)

# Chuyển logger của retriever sang DEBUG để nó in chi tiết các bước retrieve
logging.getLogger("llama_index.retrievers").setLevel(logging.DEBUG)



class ChatEngine:
    """
    Chatbot with RAG pipelines.
    Preserves chat history across all dialogues via memory buffer.
    """

    def __init__(
            self,
            llm,
            embedding_model,
            retriever,
            chat_store,
            token_limit: int = 20000,
            collection: str = 'stats_insights',
            top_k: int = 20,
            temperature: float = 0.6,
            max_tokens: int = 10000
    ):
        # Load environment variables
        self.token_limit = token_limit
        self.top_k = top_k

        # Initialize LLM & embeddings
        self.llm = llm
        self.embedding_model = embedding_model
        self.retriever = retriever
        self.chat_store = chat_store
        Settings.llm = self.llm
        Settings.embed_model = embedding_model

        # Setup persistent memory
        self.rag_engine = None
        self.chat_memory = None

    def compose(self, session_id, memory, message):
        Settings.llm = self.llm
        Settings.embed_model = self.embedding_model

        self.build_prompt(memory, message)
        self.build_memory(session_id, memory)
        self.build_chat_engine(self.retriever)

    def build_prompt(self, memory, message):
        self.rag_prompt = """
            Bạn là một chuyên gia phân tích dữ liệu thương mại điện tử, thành thạo thống kê và đưa ra những insight kinh doanh cho nền tảng TIKI.  
            Bạn có quyền truy cập vào:
              - Cơ sở dữ liệu vector chứa các thống kê tổng hợp và chỉ số thô thu thập từ TIKI:  
                giá, loại giao hàng (dropship / seller_delivery / tiki_delivery), thương hiệu, số lượt đánh giá, điểm đánh giá trung bình, số lượt yêu thích, cờ mua trả sau, số lượng hình ảnh, cờ có video, số lượng đã bán, v.v.  
              - Khả năng tính toán các chỉ số ngay lập tức (phân phối, tương quan, xu hướng, so sánh) từ những dữ liệu này.
    
            ### Khi có yêu cầu từ người dùng:
            1. **Làm rõ mục đích:**  
               - Họ muốn tóm tắt (“Top 5 thương hiệu bán chạy nhất”), phân tích phân phối (“Phân phối giá cho sản phẩm dropship”), tìm tương quan (“Mua trả sau ảnh hưởng thế nào đến số lượng bán?”), phân tích xu hướng (“Doanh số theo tuần”), hay phát hiện bất thường?
            2. **Chuyển ngữ & xác định phạm vi:**  
               - Biến yêu cầu chung chung thành nhiệm vụ phân tích cụ thể (“Cho tôi top 10 thương hiệu theo tổng số lượng đã bán trong Q2 2025”).
            3. **Truy xuất thống kê liên quan:**  
               - Lấy các chỉ số tổng hợp hoặc dữ liệu gốc đã lưu từ vector store.
            4. **Tính toán bổ sung nếu cần:**  
               - Ví dụ: phần trăm thay đổi, tốc độ tăng trưởng, hệ số tương quan, bảng pivot.
            5. **Sinh insight:**  
               - Tóm tắt kết quả chính dưới dạng **gạch đầu dòng**, nhấn mạnh các biến động, điểm bất thường, hoặc hàm ý kinh doanh.
            6. **Minh họa (nếu yêu cầu):**  
               - Gợi ý hoặc mô tả loại biểu đồ phù hợp (histogram cho phân phối, line chart cho xu hướng, scatter plot cho tương quan) và cung cấp dữ liệu thô để vẽ.
            7. **Định dạng trả lời:**  
               - Sử dụng **Markdown** với các tiêu đề rõ ràng (`### Tóm tắt`, `### Insight`, `### Khuyến nghị`).  
               - Trình bày bảng số liệu dưới dạng bảng Markdown.  
               - Khi liệt kê danh sách (thương hiệu, loại giao hàng, sản phẩm), dùng gạch đầu dòng.
    
            Nếu bạn không biết hoặc không thể tính toán được, hãy trả lời “Tôi không biết.”
        """

        self.context_prompt = """  
            Trợ lý chỉ sử dụng các số liệu đã được cung cấp ở dưới để trả lời.  
            Nếu thiếu dữ liệu hoặc chỉ số cần thiết trong context, hãy nói “Tôi không biết.”
            
            Dưới đây là những dữ liệu, tài liệu liên quan có thể cần thiết cho ngữ cảnh: 

            {{context_str}} 
            
            Yêu cầu: Dựa trên các số liệu được cung cấp, hãy trả lời câu hỏi của người dùng dưới đây một cách rõ ràng và có cấu trúc.
        """

        self.condense_prompt = f"""
            Bạn là một trợ lý AI am hiểu thương mại điện tử. Cho đoạn hội thoại dưới đây và tin nhắn mới nhất,
            hãy chuyển thành một câu hỏi độc lập, rõ ràng, **bằng tiếng Việt**:
            ===
            Hội thoại: {memory}
            Tin nhắn mới: {message}
            ===
            Hãy chỉ trả về câu hỏi rút gọn.
        """


    def build_chat_engine(self, retriever):
        self.rag_engine = CondensePlusContextChatEngine(
            retriever=retriever,
            llm=self.llm,
            system_prompt=self.rag_prompt,
            context_prompt=self.context_prompt,
            condense_prompt=self.condense_prompt,
            memory=self.chat_memory,
        )

    def build_memory(self, session_id, memory):
        self.memory = memory
        self.session_id = session_id
        # load if exists
        if memory and len(memory) > 0:
            json_memory = self.process_history()
            try:
                self.chat_store = SimpleChatStore.from_json(
                    json_memory
                )
            except Exception as e:
                print(f"Error initializing chat store from memory: {e}")

        self.chat_memory = ChatMemoryBuffer.from_defaults(
            token_limit=self.token_limit,
            chat_store=self.chat_store,
            chat_store_key=self.session_id
        )

    def process_history(self):
        chat_history = {
            "store": {
                self.session_id: []
            },
            "class_name": "SimpleChatStore"
        }
        for chat_turn in self.memory:
            message = {
                "role": chat_turn["role"],
                'additional_kwargs': {},
                "blocks": [
                    {
                        "block_type": "text",
                        "text": chat_turn["content"]
                    }
                ]
            }
            chat_history["store"][self.session_id].append(message)

        return json.dumps(chat_history)


    async def stream_chat(self, user_input: str):
        if not self.rag_engine:
            yield "ERROR: Chat engine not properly initialized."
            return

        try:
            response = self.rag_engine.stream_chat(user_input)

            if response is None:
                yield "ERROR: Failed to get streaming response"
                return

            async for chunk in self.process_streaming_response(response):
                if chunk:
                    yield chunk

        except Exception as e:
            print(f"Error in stream_chat: {str(e)}")
            yield f"ERROR: {str(e)}"

    async def process_streaming_response(self, response):
        """Process various types of streaming responses."""
        # Handle async generators
        if hasattr(response, '__aiter__'):
            async for token in response:
                if token:
                    text = self.extract_text_from_token(token)
                    if text:
                        yield text
        # Handle sync generators
        elif hasattr(response, '__iter__') and not isinstance(response, str):
            for token in response:
                if token:
                    text = self.extract_text_from_token(token)
                    if text:
                        yield text
        # Handle response objects with generators
        elif hasattr(response, 'response_gen'):
            async for chunk in self.process_streaming_response(response.response_gen):
                yield chunk
        elif hasattr(response, 'content_generator'):
            async for chunk in self.process_streaming_response(response.content_generator):
                yield chunk
        # Handle response objects with text
        elif hasattr(response, 'response'):
            yield response.response
        else:
            # Final fallback
            yield str(response)

    def extract_text_from_token(self, token):
        if isinstance(token, str):
            return token
        elif hasattr(token, 'delta'):
            return token.delta
        elif hasattr(token, 'text'):
            return token.text
        elif hasattr(token, 'content'):
            return token.content
        return None

    def persist_memory(self):
        """
        Returning chat memory in JSON format
        """
        return self.chat_store.json()

    def clear_memory(self):
        if self.chat_memory:
            self.chat_memory.reset()
        self.chat_store = SimpleChatStore()
