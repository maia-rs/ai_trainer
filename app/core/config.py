import os
import dotenv
"""Configura as variáveis de ambiente do projeto."""

dotenv.load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

# URL base da API (usada para montar URLs de mídia)
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Banco de dados: usa DB_URL quando definido, senao monta URL de MySQL.
DB_URL = os.getenv("DB_URL")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Config LLm
API_KEY = os.getenv("API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", API_KEY)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Gemini
GEMINI_API_KEY = os.getenv("API_KEY_GEMINI", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "AITrainer-Agent")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

if not DB_URL:
    DB_URL = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

# Evolution API (WhatsApp)
EVOLUTION_API_URL      = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY      = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE     = os.getenv("EVOLUTION_INSTANCE", "aitrainer")
EVOLUTION_WEBHOOK_TOKEN = os.getenv("EVOLUTION_WEBHOOK_TOKEN", "")
EVOLUTION_DEDUP_TTL_SECONDS = int(os.getenv("EVOLUTION_DEDUP_TTL_SECONDS", "600"))


if __name__ == "__main__":
    print(f"DB_HOST: {DB_HOST}")
    print(f"DB_PORT: {DB_PORT}")
    print(f"DB_NAME: {DB_NAME}")
    print(f"DB_USER: {DB_USER}")
    print(f"DB_PASSWORD: {DB_PASSWORD}")
    print(f"API_KEY:{API_KEY}")
    print(f"GROQ_API_KEY:{'set' if GROQ_API_KEY else 'missing'}")
    print(f"GROQ_MODEL:{GROQ_MODEL}")
    print(f"LANGSMITH_API_KEY:{'set' if LANGSMITH_API_KEY else 'missing'}")
    print(f"LANGSMITH_PROJECT:{LANGSMITH_PROJECT}")
    print(f"LANGSMITH_TRACING:{LANGSMITH_TRACING}")

    #testando a conexão com o banco de dados
    import mysql.connector
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            print("Conexão com o banco de dados bem-sucedida!")
    except mysql.connector.Error as e:
        print(f"Erro ao conectar ao banco de dados: {e}")

