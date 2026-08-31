import os
from dotenv import load_dotenv
from openai import OpenAI

# Line 1: Read and load environment variables from the .env file into memory
load_dotenv()

# Line 2: Create an OpenAI client instance pointed at OpenRouter's URL using your API key
client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

# Line 3: Send a request to OpenRouter asking the model to respond with "ready"
res = client.chat.completions.create(
    model=os.environ["LLM_MODEL"],
    messages=[{"role": "user", "content": "Reply with exactly the word: ready"}],
)

# Line 4: Print the response content to the terminal console
print(res.choices[0].message.content)