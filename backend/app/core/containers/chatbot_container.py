from dependency_injector import containers, providers

from app.chatbot.chat_engine import ChatEngine
from app.chatbot.small_talk_checker import SmallTalkChecker
from llama_index.core import VectorStoreIndex, load_index_from_storage, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.postprocessor.cohere_rerank import CohereRerank


class ChatbotContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    database = providers.DependenciesContainer()
    AI = providers.DependenciesContainer()

    qdrant_client = database.qdrant_client
    async_qdrant_client = database.async_qdrant_client
    neo4j_driver = database.async_neo4j_driver
    llm = AI.llm_gemini
    embed_model = AI.embed_model
    cohere_client = AI.cohere_reranker

    # Vector store components
    vector_store = providers.Singleton(
        QdrantVectorStore,
        client=qdrant_client,
        aclient=async_qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME,
        dense_vector_name="text-dense",
        sparse_vector_name="text-sparse",
        enable_hybrid=True,
    )

    # Index components
    index = providers.Singleton(
        VectorStoreIndex.from_vector_store,
        vector_store=vector_store,
        use_async=True,
    )

    # Embedding-based job retriever
    embedding_retriever = providers.Factory(
        lambda idx, top_k, mode: idx.as_retriever(similarity_top_k=top_k, vector_store_query_mode=mode),
        idx=index,
        top_k=20,
        mode="hybrid",
    )

    # Graph retrievers
    graph_retriever = providers.Singleton(
        Neo4jGraphRetriever,
        neo4j_driver=neo4j_driver,
        top_k=20
    )

    # Reranker
    reranker = providers.Singleton(
        CohereRerank,
        api_key=config.COHERE_API_TOKEN,
        top_n=10
    )

    # Hybrid retrievers
    retriever = providers.Singleton(
        HybridRetriever,
        embedding_retriever=embedding_retriever,
        graph_retriever=graph_retriever,
        reranker=reranker,
        embedding_weight=0.6,
        graph_weight=0.4,
        top_k=15
    )

    # Helper components
    small_talk_checker = providers.Singleton(SmallTalkChecker)
    chat_store = providers.Singleton(SimpleChatStore)

    # Main chat engine
    chat_engine = providers.Factory(
        ChatEngine,
        llm=llm,
        retriever=retriever,
        embedding_model=embed_model,
        chat_store=chat_store,
        checker=small_talk_checker
    )