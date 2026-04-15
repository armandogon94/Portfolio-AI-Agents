import chainlit as cl
from src.utils.logger import setup_logging
from src.config.settings import settings

setup_logging()

DOMAINS = ["general", "healthcare", "finance", "real_estate", "legal", "education", "engineering"]


@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("domain", None)
    cl.user_session.set("messages", [])

    await cl.Message(
        content=(
            f"**AI Agent System** | LLM: `{settings.llm_provider.value}` | "
            f"Embeddings: `{settings.embedding_mode.value}`\n\n"
            "I have a team of specialized agents (Researcher, Analyst, Writer, Reviewer) "
            "ready to help you.\n\n"
            "**Commands:**\n"
            "- `/domain <name>` — Switch industry domain (healthcare, finance, real_estate, legal, education, engineering)\n"
            "- `/domain general` — Reset to general mode\n\n"
            "Ask me anything to get started!"
        )
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    content = message.content.strip()

    # Handle /domain command
    if content.lower().startswith("/domain"):
        parts = content.split(maxsplit=1)
        if len(parts) < 2:
            await cl.Message(content=f"Available domains: {', '.join(DOMAINS)}").send()
            return

        domain = parts[1].strip().lower()
        if domain == "general":
            domain = None
        elif domain not in DOMAINS:
            await cl.Message(content=f"Unknown domain. Available: {', '.join(DOMAINS)}").send()
            return

        cl.user_session.set("domain", domain)
        label = domain or "general"
        await cl.Message(content=f"Switched to **{label}** domain.").send()
        return

    # Run crew
    domain = cl.user_session.get("domain")
    messages = cl.user_session.get("messages")
    messages.append({"role": "user", "content": content})

    msg = cl.Message(content="")
    await msg.send()

    try:
        msg.content = "Assembling agent crew... This may take a moment."
        await msg.update()

        from src.crew import run_crew

        result = run_crew(topic=content, domain=domain)

        msg.content = result
        await msg.update()

        messages.append({"role": "assistant", "content": result})
        cl.user_session.set("messages", messages)

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()


@cl.on_chat_end
def on_chat_end():
    pass
