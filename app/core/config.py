import os
import dotenv
"""Configura as variáveis de ambiente do projeto."""

dotenv.load_dotenv()

# Banco de dados: usa DB_URL quando definido, senao monta URL de MySQL.
DB_URL = os.getenv("DB_URL")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_URL:
    DB_URL = (
        f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


if __name__ == "__main__":
    print(f"DB_HOST: {DB_HOST}")
    print(f"DB_PORT: {DB_PORT}")
    print(f"DB_NAME: {DB_NAME}")
    print(f"DB_USER: {DB_USER}")
    print(f"DB_PASSWORD: {DB_PASSWORD}")

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