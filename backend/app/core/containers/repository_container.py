from dependency_injector import containers, providers
from app.repository import UserRepository
from app.repository.chatbot_repository import ChatbotRepository




class RepositoryContainer(containers.DeclarativeContainer):
    chatbot_repository = providers.Factory(ChatbotRepository)