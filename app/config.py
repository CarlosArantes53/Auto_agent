import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    PHONE_ID = os.getenv("PHONE_ID")
    VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    WHATSAPP_API_URL = f"https://graph.facebook.com/v16.0/{os.getenv('PHONE_ID')}/messages"
    MEDIA_DIR = "media_files"
