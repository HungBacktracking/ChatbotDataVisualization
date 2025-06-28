from dependency_injector import containers, providers
from qdrant_client import QdrantClient, AsyncQdrantClient
from app.core.database import Database


class DatabaseContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Database
    db = providers.Singleton(
        Database,
        db_url=config.DATABASE_URI,
        replica_db_url=config.REPLICA_DATABASE_URI
    )

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