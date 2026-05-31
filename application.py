import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = Groq(api_key=api_key)

def generate_notes(topic):
    prompt = f"Generate well structured notes on the topic: {topic}. Use headings, bullets and examples."

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    topic = input("Enter topic: ")
    notes = generate_notes(topic)
    print("\nGenerated Notes:\n")
    print(notes)