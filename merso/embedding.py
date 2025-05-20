from langchain_community.document_loaders import JSONLoader #TextLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter # CharacterTextSplitter é mais simples
from langchain_community.vectorstores import Weaviate
import weaviate
from dotenv import load_dotenv
import os


load_dotenv()

# Usando o JSONLoader
jq_schema = ".products[] | {code, description, price, measure_type, stock}"  # Esquema
loader = JSONLoader(
    file_path="produtos.json", 
    jq_schema=jq_schema,
    text_content=False
    )

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,                     # Tamanho máximo de cada chunk em número de caracteres
    chunk_overlap=50,                   # Sobreposição entre chunks para manter o contexto
    separators=["\n\n", "\n", " ", ""]  # Separações naturais (parágrafos, linhas, palavras)
)

docs = loader.load_and_split(
    text_splitter=text_splitter # a propriedade text_splitter é parte da função load_and_split()
)

print(f"Documentos originais: {len(docs)}")
print(f"Chunks gerados: {len(docs)}")
print(f">>> Chunks gerados <<<")

for doc in docs:
    print(doc.page_content)
    print("\n")

client = weaviate.Client(
    "http://localhost:8080",  # URL como string
    additional_headers={"X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")}
)

print(f">>> Início da vetorização de ingestão no Weaviate <<<")
vectorstore = Weaviate.from_documents(
    documents=docs,  # Lista de objetos Document do LangChain
    embedding = OpenAIEmbeddings(
    model="text-embedding-ada-002",
    #dimensions=1024 //o model text-embedding-ada-002 tem a dimensão fixa em 1536
    ),
    client=client,
    index_name="MyIndex",  # Nome do índice no Weaviate
    text_key="texto"  # Nome do campo que armazena o texto
    )

print(f">>> Fim do processamento: Chunks vetorizados <<<")
