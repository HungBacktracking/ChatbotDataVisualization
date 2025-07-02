from dependency_injector import containers, providers
from qdrant_client import QdrantClient, AsyncQdrantClient


class DatabaseContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Qdrant clients
    qdrant_client = providers.Singleton(
        QdrantClient,
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_TOKEN,
    )
    async_qdrant_client = providers.Singleton(
        AsyncQdrantClient,
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_TOKEN,
    )