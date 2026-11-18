from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    database_path: str = 'runtime/stylematch.sqlite3'
    cors_origins: str = 'http://localhost:3000,http://localhost:5173'
    llm_provider: str = 'ollama'
    vision_provider: str = 'ollama'
    ollama_base_url: str = 'http://127.0.0.1:11434'
    ollama_model: str = 'qwen3:8b'
    ollama_vision_model: str = ''
    gemini_api_key: str = ''
    gemini_model: str = ''
    fashn_api_key: str = ''
    serpapi_api_key: str = ''
    session_days: int = 7
    max_tryons_per_hour: int = 5
    @property
    def origins(self):
        return [x.strip() for x in self.cors_origins.split(',') if x.strip()]

settings = Settings()
