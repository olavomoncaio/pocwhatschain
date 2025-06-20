from langchain_community.document_loaders import JSONLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Weaviate
import weaviate
from dotenv import load_dotenv
import os

load_dotenv()

# Configuração do Weaviate v3
client = weaviate.Client(
    url="http://localhost:8080",
    additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
)

# Carregar documentos (seu código existente)
jq_schema = ".produtos[] | {codigo, nome, descricao, preco, unidade, fragmentavel}"
loader = JSONLoader(
    file_path="produtos.json", 
    jq_schema=jq_schema,
    text_content=False
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

docs = loader.load_and_split(text_splitter=text_splitter)

print(f"Documentos originais: {len(docs)}")
print(f"Chunks gerados: {len(docs)}")

# Verificar e criar schema de forma mais robusta
schema = client.schema.get()
class_names = [cls["class"] for cls in schema["classes"]]
index_name = "MyIndex"

if index_name not in class_names:
    class_obj = {
        "class": index_name,
        "vectorizer": "text2vec-openai",
        "moduleConfig": {
            "text2vec-openai": {
                "model": "text-embedding-ada-002",
                "type": "text"
            }
        },
        "properties": [
            {
                "name": "texto",
                "dataType": ["text"],
                "moduleConfig": {
                    "text2vec-openai": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            }
        ]
    }
    client.schema.create_class(class_obj)
    print(f"Schema '{index_name}' criado com sucesso!")
else:
    print(f"Schema '{index_name}' já existe.")

# Ingestão dos documentos
try:
    vectorstore = Weaviate.from_documents(
        client=client,
        documents=docs,
        embedding=OpenAIEmbeddings(model="text-embedding-ada-002"),
        index_name=index_name,
        text_key="texto"
    )
    print("Documentos ingeridos com sucesso!")
except Exception as e:
    print(f"Erro ao ingerir documentos: {str(e)}")
finally:
    # Encerramento correto para Weaviate v3
    if 'client' in locals():
        del client  # Na v3, não há método close(), apenas liberamos a referência
        print("Conexão encerrada.")