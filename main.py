from fastapi import FastAPI
from dotenv import load_dotenv
from routes import process_message
import logging

load_dotenv()

app = FastAPI()
app.include_router(process_message.router)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
