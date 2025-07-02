from dependency_injector import containers, providers
import logging
from app.core.config import configs
from app.core.containers.chatbot_container import ChatbotContainer
from app.core.containers.database_container import DatabaseContainer
from app.core.containers.ai_container import AIContainer
from app.core.containers.service_container import ServiceContainer

class ApplicationContainer(containers.DeclarativeContainer):
    logger = logging.getLogger(__name__)
    
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.endpoints.chat"
        ]
    )

    config = providers.Configuration()
    config.override(configs.dict())

    database = providers.Container(
        DatabaseContainer,
        config=config,
    )

    AI = providers.Container(
        AIContainer,
        config=config,
    )

    chatbot = providers.Container(
        ChatbotContainer,
        config=config,
        database=database,
        AI=AI
    )

    services = providers.Container(
        ServiceContainer,
        config=config,
        chat_engine=chatbot.chat_engine
    )
