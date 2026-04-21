
import os
from google import genai
from congen.config.settings import settings

api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
client = genai.Client(api_key=api_key)

print("=== client.operations.get doc ===")
if hasattr(client, "operations"):
    print(client.operations.get.__doc__)
else:
    print("client.operations does not exist")

print("\n=== client.models.generate_videos doc ===")
print(client.models.generate_videos.__doc__)
