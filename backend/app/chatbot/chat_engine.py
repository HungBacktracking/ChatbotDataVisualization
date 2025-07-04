from typing import Optional, Dict, Any
from app.schema.chat_schema import ChartResponse, ChartData, ChartConfig
from llama_index.core import Settings
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.chat_engine import (
    CondensePlusContextChatEngine
)
import re


import nest_asyncio
import json
import asyncio
from loguru import logger
import logging


nest_asyncio.apply()

# Bật logging toàn cục mức INFO
# logging.basicConfig(level=logging.DEBUG)

# Chuyển logger của retriever sang DEBUG để nó in chi tiết các bước retrieve
# logging.getLogger("llama_index.retrievers").setLevel(logging.DEBUG)


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
        self.needChart = False

        # Store current query for chart extraction
        self.current_query = None

    def compose(self, session_id, memory, message):
        Settings.llm = self.llm
        Settings.embed_model = self.embedding_model

        self.current_query = message
        self.needChart = self.detect_chart_intent(message)
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
               - Họ muốn tóm tắt ("Top 5 thương hiệu bán chạy nhất"), phân tích phân phối ("Phân phối giá cho sản phẩm dropship"), tìm tương quan ("Mua trả sau ảnh hưởng thế nào đến số lượng bán?"), phân tích xu hướng ("Doanh số theo tuần"), hay phát hiện bất thường?
            2. **Chuyển ngữ & xác định phạm vi:**  
               - Biến yêu cầu chung chung thành nhiệm vụ phân tích cụ thể ("Cho tôi top 10 thương hiệu theo tổng số lượng đã bán trong Q2 2025").
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

            Nếu bạn không biết hoặc không thể tính toán được, hãy trả lời "Tôi không biết."
        """

        self.chart_prompt = f"""
            Bạn là một chuyên gia phân tích dữ liệu thương mại điện tử, thành thạo thống kê và đưa ra những insight kinh doanh cho nền tảng TIKI.  
            Bạn có quyền truy cập vào:
              - Cơ sở dữ liệu vector chứa các thống kê tổng hợp và chỉ số thô thu thập từ TIKI:  
                giá, loại giao hàng (dropship / seller_delivery / tiki_delivery), thương hiệu, số lượt đánh giá, điểm đánh giá trung bình, số lượt yêu thích, cờ mua trả sau, số lượng hình ảnh, cờ có video, số lượng đã bán, v.v.  
              - Khả năng tính toán các chỉ số ngay lập tức (phân phối, tương quan, xu hướng, so sánh) từ những dữ liệu này.
            Phân tích văn bản sau và trích xuất dữ liệu có cấu trúc phù hợp để vẽ biểu đồ phục vụ nhu cầu phân tích dữ liệu.

            Câu hỏi: {message}

            Hãy trả về JSON với format sau (chỉ trả về JSON, không có text khác):
            {{
                "chart_type": "bar|line|histogram|pie|scatter|doughnut",
                "title": "Tiêu đề biểu đồ",
                "x_label": "Nhãn trục X (nếu có)",
                "y_label": "Nhãn trục Y (nếu có)",
                "labels": ["label1", "label2", ...],
                "datasets": [
                    {{
                        "label": "Tên dataset",
                        "data": [value1, value2, ...],
                        "backgroundColor": "auto",
                        "borderColor": "auto"
                    }}
                ],
                "description": "Mô tả ngắn gọn về biểu đồ"
            }}

            Và đối với scatter:
                - Bỏ hoặc để [] cho "labels"
                - Trong "datasets.data", mỗi phần tử phải là object {{ "x": số, "y": số }}
                Ví dụ:
                    "data": [
                        {{ "x": 10, "y": 200 }},
                        {{ "x": 15, "y": 350 }},
                        …
                    ],

            Lưu ý:
            - Chọn chart_type phù hợp: bar cho so sánh, line cho xu hướng, pie cho tỷ lệ, vân vân.
            - Trích xuất tất cả số liệu từ văn bản
            - Đảm bảo labels và data có cùng độ dài
            - Nếu không thể trích xuất dữ liệu hoặc không đủ dữ liệu cần thiết, trả về null
        """

        self.context_prompt = """  
            Trợ lý chỉ sử dụng các số liệu đã được cung cấp ở dưới để trả lời.  
            Nếu thiếu dữ liệu hoặc chỉ số cần thiết trong context, hãy nói "Tôi không biết."

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
            system_prompt=self.chart_prompt if self.needChart == True else self.rag_prompt,
            context_prompt=self.context_prompt,
            condense_prompt=self.condense_prompt,
            memory=self.chat_memory
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

        return json.dumps(chat_history, ensure_ascii=False)

    def detect_chart_intent(self, query: str) -> bool:
        """
        Detects if the query requires chart visualization.
        """
        try:
            detection_prompt = f"""
                Analyze the following query and response to determine if a chart/graph visualization was asked by user.

                Query: {query}

                Consider the factor: Does the query explicitly ask for visualization (chart, graph, biểu đồ, visual)?


                Reply with only "YES" if a chart was asked, or "NO" if not needed.
            """

            llm_response = self.llm.complete(detection_prompt)
            result = llm_response.text.strip().upper()

            return "YES" in result

        except Exception as e:
            logger.error(f"Error in LLM chart intent detection: {e}")
            return False

    def extract_chart_data(self, user_input: str) -> Optional[ChartResponse]:
        """
        Extracts structured data from response and formats it for chart visualization.
        """
        try:

            llm_response = self.rag_engine.chat(user_input)
            extracted_text = llm_response.response.strip()

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', extracted_text, re.DOTALL)
            if not json_match:
                return None

            extracted_data = json.loads(json_match.group())

            if not extracted_data or extracted_data == "null":
                return None

            # Create ChartResponse
            chart_data = ChartData(
                labels=extracted_data.get('labels', []),
                datasets=extracted_data.get('datasets', [])
            )

            chart_config = ChartConfig(
                type=extracted_data.get('chart_type', 'bar'),
                title=extracted_data.get('title'),
                x_label=extracted_data.get('x_label'),
                y_label=extracted_data.get('y_label')
            )

            return ChartResponse(
                chart_data=chart_data,
                chart_config=chart_config,
                description=extracted_data.get('description')
            )

        except Exception as e:
            logger.error(f"Error extracting chart data: {e}")
            return None

    def format_for_frontend(self, chart_response: ChartResponse) -> Dict[str, Any]:
        """
        Formats chart response for frontend consumption.
        """
        return {
            "type": "chart",
            "data": chart_response.chart_data.model_dump(),
            "config": chart_response.chart_config.model_dump(),
            "description": chart_response.description
        }

    async def stream_chat(self, user_input: str):
        if not self.rag_engine:
            yield "ERROR: Chat engine not properly initialized."
            return

        try:
            if self.needChart:
                chart_response = self.extract_chart_data(user_input)
                if chart_response:
                    chart_data = self.format_for_frontend(chart_response)
                    yield json.dumps(chart_data, ensure_ascii=False)
                    return
                else:
                    yield "ERROR: Failed to get chart response"
                    return

            response = self.rag_engine.stream_chat(user_input)

            if response is None:
                yield "ERROR: Failed to get streaming response"
                return

            # Collect full response for chart extraction
            full_response = ""

            async for chunk in self.process_streaming_response(response):
                if chunk:
                    # Check for errors
                    if chunk.startswith("ERROR:"):
                        yield chunk
                        return

                    # Accumulate response
                    full_response += chunk

                    # Yield text chunk
                    yield json.dumps({
                        "type": "text",
                        "content": chunk
                    }, ensure_ascii=False)

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
