from fastapi import FastAPI
from dotenv import load_dotenv
from routes import process_message
from routes import estoque
import logging

load_dotenv()

app = FastAPI()
app.include_router(process_message.router)
app.include_router(estoque.router, prefix="/estoque")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
