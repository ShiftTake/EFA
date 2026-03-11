import os

class Settings:
    PROJECT_NAME: str = "EditForAll"
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

settings = Settings()
