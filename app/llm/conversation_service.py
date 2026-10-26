# from typing import List, Optional
# import uuid
# import logging
# from app.memory.manager import MemoryManager, ChatMessage, Role
# from app.retrieval.retriever import Retriever
# from app.retrieval.models import RetrievalQuery
# from app.llm.prompt_builder import PromptBuilder
# from app.llm.gateway import LLMGateway
# from app.observability.audit_logger import audit_logger
# from app.observability.metrics import LLM_LATENCY, LLM_TOKEN_USAGE
# import time

# logger = logging.getLogger(__name__)

# class ConversationService:
#     def __init__(self):
#         self.memory_manager = MemoryManager()
#         self.retriever = Retriever()
#         self.prompt_builder = PromptBuilder()
#         self.llm_gateway = LLMGateway()

#     async def chat(self, session_id: str, query: str, options: dict = None) -> str:
#         options = options or {}
#         top_k = options.get("top_k", 3)
#         use_reranker = options.get("use_reranker", True)
#         model = options.get("model", "gpt-3.5-turbo")
#         temperature = options.get("temperature", 0.7)
        
#         start_time = time.time()
        
#         # Audit Query
#         audit_logger.log_query(session_id, query)
        
#         # 1. Retrieve
#         logger.info(f"Session {session_id}: Processing query '{query}'")
        
#         retrieval_query = RetrievalQuery(query=query, top_k=top_k, use_reranker=use_reranker)
#         retrieval_resp = self.retriever.retrieve(retrieval_query)
        
#         # 2. Get History
#         history = self.memory_manager.get_history(session_id)
        
#         # 3. Build Prompt (Could pass citation_mode here if needed)
#         messages = self.prompt_builder.build_prompt(
#             query=query, 
#             history=history, 
#             retrieval_results=retrieval_resp.results
#         )
        
#         # 4. Generate Answer
#         llm_start = time.time()
#         answer_content = await self.llm_gateway.generate_response(messages, model=model, temperature=temperature)
#         llm_duration = time.time() - llm_start
        
#         # Record Metrics
#         LLM_LATENCY.labels(model=model).observe(llm_duration)
        
#         # 5. Update Memory
#         self.memory_manager.add_message(session_id, ChatMessage(role=Role.USER, content=query))
#         self.memory_manager.add_message(session_id, ChatMessage(role=Role.ASSISTANT, content=answer_content))
        
#         # Audit Response
#         total_duration_ms = (time.time() - start_time) * 1000
#         audit_logger.log_response(session_id, answer_content, total_duration_ms)
        
#         return answer_content

#     async def chat_stream(self, session_id: str, query: str, options: dict = None):
#         options = options or {}
#         top_k = options.get("top_k", 3)
#         use_reranker = options.get("use_reranker", True)
#         model = options.get("model", "gpt-3.5-turbo")
#         temperature = options.get("temperature", 0.7)

#         start_time = time.time()
        
#         # Audit Query
#         audit_logger.log_query(session_id, query)
        
#         # 1. Retrieve
#         logger.info(f"Session {session_id}: Processing query '{query}'")
        
#         filters = options.get("filters")
#         retrieval_query = RetrievalQuery(query=query, top_k=top_k, use_reranker=use_reranker, filters=filters)
#         retrieval_resp = self.retriever.retrieve(retrieval_query)
        
#         # 2. Get History
#         history = self.memory_manager.get_history(session_id)
        
#         # 3. Build Prompt
#         messages = self.prompt_builder.build_prompt(
#             query=query, 
#             history=history, 
#             retrieval_results=retrieval_resp.results
#         )
        
#         # 4. Stream Answer
#         llm_start = time.time()
#         full_response = ""
        
#         # Yield Sources first (metadata event)
#         sources_data = [
#             {"source_filename": res.metadata.get("source_filename"), "page_number": res.metadata.get("page_number"), "score": res.score} 
#             for res in retrieval_resp.results
#         ]
#         yield {"sources": sources_data}
        
#         try:
#             async for chunk in self.llm_gateway.stream_response(messages, model=model, temperature=temperature):
#                 full_response += chunk
#                 yield chunk
#         finally:
#             llm_duration = time.time() - llm_start
            
#             # Record Metrics (Approximate for streaming)
#             LLM_LATENCY.labels(model=model).observe(llm_duration)
            
#             # 5. Update Memory (only if we got a response)
#             if full_response:
#                 self.memory_manager.add_message(session_id, ChatMessage(role=Role.USER, content=query))
#                 self.memory_manager.add_message(session_id, ChatMessage(role=Role.ASSISTANT, content=full_response))
                
#                 # Audit Response
#                 total_duration_ms = (time.time() - start_time) * 1000
#                 audit_logger.log_response(session_id, full_response, total_duration_ms)

#     def create_session(self) -> str:
#         return str(uuid.uuid4())

# conversation_service = ConversationService()




from typing import Optional
import uuid
import logging
import time

from app.llm.memory.manager import MemoryManager, ChatMessage, Role
from app.retrieval.retriever import Retriever
from app.retrieval.models import RetrievalQuery
from app.llm.prompt_builder import PromptBuilder
from app.llm.gateway import LLMGateway
from app.observability.audit_logger import audit_logger
from app.observability.metrics import LLM_LATENCY, LLM_TOKEN_USAGE

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.retriever = Retriever()
        self.prompt_builder = PromptBuilder()
        self.llm_gateway = LLMGateway()

        self.default_model = "openai/gpt-oss-120b"

    async def chat(
        self,
        session_id: str,
        query: str,
        options: dict = None,
    ) -> str:
        options = options or {}

        top_k = options.get("top_k", 3)
        use_reranker = options.get("use_reranker", True)
        model = options.get("model", self.default_model)
        temperature = options.get("temperature", 0.7)

        start_time = time.time()

        # 1. Audit query
        audit_logger.log_query(session_id, query)

        logger.info(
            "Session %s: Processing query",
            session_id,
        )

        # 2. Retrieve relevant documents
        retrieval_query = RetrievalQuery(
            query=query,
            top_k=top_k,
            use_reranker=use_reranker,
        )

        retrieval_resp = self.retriever.retrieve(retrieval_query)

        # 3. Retrieve conversation history
        history = self.memory_manager.get_history(session_id)

        # 4. Build the RAG prompt
        messages = self.prompt_builder.build_prompt(
            query=query,
            history=history,
            retrieval_results=retrieval_resp.results,
        )

        # 5. Generate the answer through Groq
        llm_start = time.time()

        answer_content = await self.llm_gateway.generate_response(
            messages,
            model=model,
            temperature=temperature,
        )

        llm_duration = time.time() - llm_start

        # 6. Record latency metrics
        LLM_LATENCY.labels(model=model).observe(llm_duration)

        # 7. Update conversation memory
        self.memory_manager.add_message(
            session_id,
            ChatMessage(role=Role.USER, content=query),
        )

        self.memory_manager.add_message(
            session_id,
            ChatMessage(role=Role.ASSISTANT, content=answer_content),
        )

        # 8. Audit response
        total_duration_ms = (time.time() - start_time) * 1000

        audit_logger.log_response(
            session_id,
            answer_content,
            total_duration_ms,
        )

        return answer_content

    async def chat_stream(
        self,
        session_id: str,
        query: str,
        options: dict = None,
    ):
        options = options or {}

        top_k = options.get("top_k", 3)
        use_reranker = options.get("use_reranker", True)
        model = options.get("model", self.default_model)
        temperature = options.get("temperature", 0.7)
        filters = options.get("filters")

        start_time = time.time()

        # 1. Audit query
        audit_logger.log_query(session_id, query)

        logger.info(
            "Session %s: Processing streaming query",
            session_id,
        )

        # 2. Retrieve relevant documents
        retrieval_query = RetrievalQuery(
            query=query,
            top_k=top_k,
            use_reranker=use_reranker,
            filters=filters,
        )

        retrieval_resp = self.retriever.retrieve(retrieval_query)

        # 3. Retrieve conversation history
        history = self.memory_manager.get_history(session_id)

        # 4. Build the RAG prompt
        messages = self.prompt_builder.build_prompt(
            query=query,
            history=history,
            retrieval_results=retrieval_resp.results,
        )

        llm_start = time.time()
        full_response = ""

        # 5. Send retrieved source metadata first
        sources_data = [
            {
                "source_filename": res.metadata.get("source_filename"),
                "page_number": res.metadata.get("page_number"),
                "score": res.score,
            }
            for res in retrieval_resp.results
        ]

        yield {"sources": sources_data}

        try:
            # 6. Stream the answer
            async for chunk in self.llm_gateway.stream_response(
                messages,
                model=model,
                temperature=temperature,
            ):
                full_response += chunk
                yield chunk

        finally:
            llm_duration = time.time() - llm_start

            # 7. Record latency metrics
            LLM_LATENCY.labels(model=model).observe(llm_duration)

            # 8. Save conversation only if a response was generated
            if full_response:
                self.memory_manager.add_message(
                    session_id,
                    ChatMessage(role=Role.USER, content=query),
                )

                self.memory_manager.add_message(
                    session_id,
                    ChatMessage(
                        role=Role.ASSISTANT,
                        content=full_response,
                    ),
                )

                total_duration_ms = (
                    time.time() - start_time
                ) * 1000

                audit_logger.log_response(
                    session_id,
                    full_response,
                    total_duration_ms,
                )

    def create_session(self) -> str:
        return str(uuid.uuid4())


conversation_service = ConversationService()