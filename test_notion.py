from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

# list all methods available
print(dir(notion.databases))