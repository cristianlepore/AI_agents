import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MAIL_SERVER = os.getenv("MAIL_SERVER")
GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP = os.getenv("GMAIL_APP")
MURENA_SERVER = os.getenv("MURENA_SERVER")
MURENA_USERNAME = os.getenv("MURENA_USERNAME")
MURENA_APP = os.getenv("MURENA_APP")
IMAP_PORT = os.getenv("IMAP_PORT")

GROQ_MODEL = "openai/gpt-oss-120b"

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
