from tomato_ai.config import settings
from strands import Agent
from strands.models.ollama import OllamaModel

turbo_120_ollama_model = OllamaModel(
    ollama_client_args={
        "headers": {
            "Authorization": settings.OLLAMA_API_KEY,
        },
    },
    host="https://ollama.com",
    model_id="gpt-oss:120b",
)

turbo_20_ollama_model = OllamaModel(
    ollama_client_args={
        "headers": {
            "Authorization": settings.OLLAMA_API_KEY,
        },
    },
    host="https://ollama.com",
    model_id="gpt-oss:20b",
)

agent = Agent(
    model=turbo_20_ollama_model,
    system_prompt=""
)
