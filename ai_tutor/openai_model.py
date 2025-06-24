import os
import openai

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)


def clean_conversation_history(messages: list, max_history: int = 8) -> list:
    """
    Clean and prepare conversation history for better context handling
    """
    if not messages or not isinstance(messages, list):
        return []

    cleaned_messages = []

    for message in messages:
        if not isinstance(message, dict):
            continue

        role = message.get("role", "").strip().lower()
        content = message.get("content", "").strip()

        # Skip invalid messages
        if not role or not content or role not in ["user", "assistant"]:
            continue

        # Skip very short messages
        if len(content) < 2:
            continue

        # Skip error messages
        error_keywords = [
            "timeout",
            "error",
            "failed",
            "exception",
            "couldn't generate",
            "internal error",
        ]
        if any(keyword in content.lower() for keyword in error_keywords):
            continue

        # Skip consecutive duplicates
        if (
            cleaned_messages
            and cleaned_messages[-1]["role"] == role
            and cleaned_messages[-1]["content"] == content
        ):
            continue

        # Skip repeated user questions
        if role == "user" and len(cleaned_messages) >= 2:
            recent_user_messages = [
                msg["content"] for msg in cleaned_messages[-4:] if msg["role"] == "user"
            ]
            if content in recent_user_messages:
                continue

        # Truncate very long messages
        if len(content) > 1500:
            content = content[:1500] + "... [truncated]"

        cleaned_messages.append({"role": role, "content": content})

    # Keep only recent messages
    if len(cleaned_messages) > max_history:
        cleaned_messages = cleaned_messages[-max_history:]

    return cleaned_messages


def create_conversation_summary(cleaned_messages: list) -> str:
    """Create a focused conversation summary for the AI"""
    if not cleaned_messages:
        return "This is the start of our conversation."

    # Take last 4 messages for context
    recent_messages = cleaned_messages[-4:]

    summary_lines = []
    for msg in recent_messages:
        role = msg["role"].upper()
        content = msg["content"]

        # Truncate for summary
        if len(content) > 120:
            content = content[:120] + "..."

        summary_lines.append(f"{role}: {content}")

    return "\n".join(summary_lines)


def get_tutor_model(subject: str, messages: list):
    """Create AI tutor with improved prompt and message handling"""

    # Clean and prepare messages
    cleaned_messages = clean_conversation_history(messages)
    conversation_summary = create_conversation_summary(cleaned_messages)

    # Get subject display name
    subject_display = dict(
        [
            ("math", "Mathematics"),
            ("biology", "Biology"),
            ("physics", "Physics"),
            ("chemistry", "Chemistry"),
            ("history", "History"),
            ("geography", "Geography"),
            ("computer_science", "Computer Science"),
            ("art", "Art"),
            ("music", "Music"),
            ("kazakh", "Kazakh Language"),
            ("russian", "Russian Language"),
            ("english", "English Language"),
        ]
    ).get(subject, subject.title())

    system_prompt = f"""You are an expert AI tutor specializing EXCLUSIVELY in {subject_display}.

CRITICAL RULES:
• ONLY answer questions about {subject_display}
• If asked about other topics, redirect: "I'm your {subject_display} tutor! Let's focus on {subject_display}. What would you like to learn?"
• Stay in character as a {subject_display} specialist at all times

YOUR EXPERTISE: {subject_display}
• Help students understand concepts and solve problems
• Provide clear, step-by-step explanations
• Adapt to the student's level and pace
• Build on previous conversation topics

CONVERSATION CONTEXT:
{conversation_summary}

RESPONSE STYLE:
• Use the same language as the student (English/Russian/Kazakh)
• Be encouraging and patient
• Use emojis sparingly (1-2 per response)
• Format math with LaTeX when applicable
• Give examples and check understanding
• Reference previous topics when relevant

Remember: You ONLY teach {subject_display}. Redirect any off-topic questions immediately."""

    # Prepare chat messages
    chat_messages = [{"role": "system", "content": system_prompt}]

    # Add cleaned conversation history
    for msg in cleaned_messages:
        chat_messages.append({"role": msg["role"], "content": msg["content"]})

    def chat():
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=chat_messages,
                temperature=0.2,  # Low for consistency
                max_tokens=1200,
                presence_penalty=0.3,
                frequency_penalty=0.3,
                top_p=0.9,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return f"⚠️ I'm having trouble generating a response right now. Please try again in a moment."

    return chat
