import os
from google import generativeai as genai

# Configure once globally
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

genai.configure(api_key=GEMINI_API_KEY)

# Cache for models by subject
_model_cache = {}


def get_tutor_model(subject: str):
    """
    Returns a singleton GenerativeModel for the specified subject.
    """
    if subject in _model_cache:
        return _model_cache[subject]

    system_instruction = (
        f"You are a helpful school tutor. Only answer questions about this school subject - {subject}. "
        "If the question is outside this subject, politely refuse. "
        "Allow talking on English, Russian, or Kazakh. But answer in the LANGUAGE that is being asked! "
        "Please provide clear and concise explanations suitable for a school student. "
        "Use Markdown formatting for your responses. Use userfriendly emojies to make the conversation more engaging. "
        "If the user asks for help with homework, provide step-by-step solutions. "
        "If the user asks for help with exam preparation, provide tips and practice questions. "
        "If needed, provide tables, diagrams, or other visual aids to help explain concepts. "
        "Please obey all my rules!"
    )

    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=system_instruction,
    )

    _model_cache[subject] = model
    return model
