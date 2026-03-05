from dotenv import load_dotenv
load_dotenv()

import os
from openai import OpenAI

api_key = os.getenv("ZHIPUAI_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.z.ai/api/openai")

try:
    response = client.chat.completions.create(
        model="GLM-4.7",
        messages=[{"role": "user", "content": "你好"}],
        max_tokens=50
    )
    print("Response:", response)
    print("Content:", response.choices[0].message.content)
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
