from dependency_injector import containers, providers
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.gemini import Gemini



class AIContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    llm_gemini = providers.Singleton(
        Gemini,
        model_name='models/gemini-2.0-flash',
        api_key=config.GEMINI_TOKEN,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE
    )

    embed_model = providers.Singleton(
        HuggingFaceEmbedding,
        model_name=config.EMBEDDING_MODEL_NAME
    )

