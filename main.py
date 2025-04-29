from fastapi import FastAPI
from pydantic import BaseModel
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Setup LangChain

class HelloRequest(BaseModel):
    nome: str

@app.post("/hello")
async def hello(req: HelloRequest):
    resposta = "oi olavo, " + req.nome
    return {"resposta": resposta }
