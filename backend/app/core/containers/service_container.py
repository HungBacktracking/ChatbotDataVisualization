from dependency_injector import containers, providers
from app.services.chatbot_service import ChatbotService


class ServiceContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    chat_engine = providers.Dependency()


    chatbot_service = providers.Factory(
        ChatbotService,
        chat_engine=chat_engine
    )