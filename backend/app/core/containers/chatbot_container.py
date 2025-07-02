from dependency_injector import containers, providers

from app.chatbot.chat_engine import ChatEngine
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.storage.chat_store import SimpleChatStore


class ChatbotContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    database = providers.DependenciesContainer()
    AI = providers.DependenciesContainer()

    qdrant_client = database.qdrant_client
    async_qdrant_client = database.async_qdrant_client
    llm = AI.llm_gemini
    embed_model = AI.embed_model

    # Vector store components
    vector_store = providers.Singleton(
        QdrantVectorStore,
        client=qdrant_client,
        aclient=async_qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME,
        dense_vector_name="text-dense",
        enable_hybrid=False
    )

    # Index components
    index = providers.Singleton(
        VectorStoreIndex.from_vector_store,
        vector_store=vector_store,
        embed_model=embed_model,
        use_async=True,
    )

    # Embedding-based job retriever
    embedding_retriever = providers.Factory(
        lambda idx, top_k: idx.as_retriever(similarity_top_k=top_k),
        idx=index,
        top_k=20,
    )



    # Helper components
    chat_store = providers.Singleton(SimpleChatStore)

    # Main chat engine
    chat_engine = providers.Factory(
        ChatEngine,
        llm=llm,
        retriever=embedding_retriever,
        embedding_model=embed_model,
        chat_store=chat_store,
    )