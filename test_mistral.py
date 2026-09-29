import os

from dotenv import load_dotenv
from mistralai.client import Mistral


load_dotenv()

api_key = os.getenv("MISTRAL_API_KEY")

if not api_key:
    raise ValueError(
        "MISTRAL_API_KEY was not found."
    )

client = Mistral(api_key=api_key)

response = client.chat.complete(
    model="mistral-small-latest",
    messages=[
        {
            "role": "user",
            "content": (
                "Explain in two sentences why "
                "artificial intelligence is important "
                "in higher education."
            )
        }
    ]
)

print(response.choices[0].message.content)