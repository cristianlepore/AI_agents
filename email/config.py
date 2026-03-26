import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MAIL_SERVER = os.getenv("MAIL_SERVER")
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP = os.getenv("GMAIL_APP")
GROQ_MODEL = "llama-3.3-70b-versatile"

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
