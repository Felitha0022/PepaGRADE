from dotenv import load_dotenv
import os

from openai import OpenAI


# Load .env
load_dotenv()


# Get API key
api_key = os.getenv("DEEPSEEK_API_KEY")


if not api_key:
    print("ERROR: DEEPSEEK_API_KEY was not found in .env")
    exit()


print("API key found.")
print("Testing DeepSeek...")


# Create DeepSeek client
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)


try:

    response = client.chat.completions.create(

        model="deepseek-flash",

        messages=[
            {
                "role": "user",
                "content": (
                    'Return exactly this JSON: '
                    '{"status": "DeepSeek connection successful"}'
                )
            }
        ],

        response_format={
            "type": "json_object"
        },

        max_tokens=100
    )


    result = response.choices[0].message.content

    print()
    print("SUCCESS!")
    print("DeepSeek response:")
    print(result)


except Exception as error:

    print()
    print("DEEPSEEK TEST FAILED")
    print()
    print(error)