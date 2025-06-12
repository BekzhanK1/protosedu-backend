import os
import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)


def get_tutor_model(subject: str, messages: list):
    system_prompt = (
        f"You are a friendly and highly knowledgeable school tutor specializing in '{subject}'.\n\n"
        "🎯 Your job is to help students understand this subject clearly and confidently.\n"
        "✅ Only answer questions related to this subject.\n"
        "❌ Politely decline any question outside the subject.\n\n"
        "🌍 You understand English, Russian, and Kazakh. Always respond in the language used by the student.\n\n"
        "📘 Keep explanations simple and clear, suitable for school students.\n"
        "🧩 Use step-by-step solutions for homework or math problems.\n"
        "🎓 Provide tips, practice questions, or revision help for exams.\n"
        # "📊 Include tables or visuals if needed (as Markdown).\n"
        "📝 Format your answers with Latex and use relevant emojis to make the explanation more engaging!\n"
        "📏 Stay helpful, honest, and concise!"
    )

    chat_messages = [{"role": "system", "content": system_prompt}] + messages

    def chat():
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4o" if you want
            messages=chat_messages,
            temperature=0.7,
        )
        return response.choices[0].message.content  # updated field name

    return chat
