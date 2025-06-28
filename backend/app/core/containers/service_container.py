from dependency_injector import containers, providers
from app.services.chatbot_service import ChatbotService


class ServiceContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    repos = providers.DependenciesContainer()
    chat_engine = providers.Dependency()


    chatbot_service = providers.Factory(
        ChatbotService,
        chatbot_repository=repos.chatbot_repository,
        chat_engine=chat_engine
    )