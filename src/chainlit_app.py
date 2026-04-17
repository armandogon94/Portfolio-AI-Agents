import asyncio
import logging
import threading

import chainlit as cl

from src.config.settings import settings
from src.exceptions import AppError
from src.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

DOMAINS = ["general", "healthcare", "finance", "real_estate", "legal", "education", "engineering"]


def _demo_scenarios_help() -> str:
    """Render the available demo scenarios as a Chainlit-friendly markdown list.

    Slice-28: the /demo command lists deterministic scenarios served by the
    FakeLLM when DEMO_MODE=true. Users can copy-paste the command shown to
    run any scenario without hitting Ollama or Anthropic.
    """
    try:
        from src.demo import load_scenarios

        scenarios = load_scenarios()
    except Exception as exc:  # pragma: no cover — demo module optional at dev time
        return f"Demo scenarios unavailable: {exc}"

    if not scenarios:
        return "No demo scenarios registered."
    lines = [
        "**Canned demo scenarios** (set `DEMO_MODE=true` + `DEMO_SCENARIO=<name>`):",
        "",
    ]
    for name, entry in sorted(scenarios.items()):
        desc = entry.get("description", "")
        lines.append(f"- `{name}` — {desc}")
    lines.append("")
    lines.append(
        "Run locally: `DEMO_MODE=true DEMO_SCENARIO=<name> uv run python scripts/demo.py --scenario <name>`"
    )
    return "\n".join(lines)


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

    # Handle /demo command — list canned deterministic scenarios (slice-28).
    if content.lower().startswith("/demo"):
        await cl.Message(content=_demo_scenarios_help()).send()
        return

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

    msg = cl.Message(content="Assembling agent crew...")
    await msg.send()

    try:
        loop = asyncio.get_running_loop()
        progress_lines: list[str] = []
        progress_lock = threading.Lock()

        def on_step(step: object) -> None:
            """Called by CrewAI after each agent step (runs in crew thread)."""
            from crewai.agents.crew_agent_executor import AgentAction, AgentFinish

            if isinstance(step, AgentAction):
                tool_input = str(step.tool_input)
                snippet = tool_input[:120] + "..." if len(tool_input) > 120 else tool_input
                line = f"**[{step.tool}]** {snippet}"
            elif isinstance(step, AgentFinish):
                thought = step.thought[:150] + "..." if len(step.thought) > 150 else step.thought
                line = f"**Done:** {thought}"
            else:
                line = str(step)[:200]

            with progress_lock:
                progress_lines.append(line)
                snapshot = list(progress_lines)

            asyncio.run_coroutine_threadsafe(_update_progress(msg, snapshot), loop)

        from src.crew import build_crew

        prior_context = _format_prior_context(messages[:-1])  # exclude the just-added user msg
        crew = build_crew(domain=domain, step_callback=on_step)
        result = await asyncio.to_thread(
            crew.kickoff, inputs={"topic": content, "prior_context": prior_context}
        )

        msg.content = str(result)
        await msg.update()

        messages.append({"role": "assistant", "content": str(result)})
        cl.user_session.set("messages", messages)

    except Exception as e:
        logger.exception("Crew execution failed")
        user_msg = str(e) if isinstance(e, AppError) else "An unexpected error occurred. Please try again."
        msg.content = f"Error: {user_msg}"
        await msg.update()


async def _update_progress(msg: cl.Message, lines: list[str]) -> None:
    """Update the Chainlit message with current progress lines."""
    msg.content = "\n\n".join(lines) + "\n\n_Running..._"
    await msg.update()


def _format_prior_context(messages: list[dict], limit: int = 3) -> str:
    """Build a prior context string from the last N user/assistant message pairs.

    Args:
        messages: Conversation history list of {role, content} dicts.
        limit: Maximum number of prior topic summaries to include.

    Returns:
        A formatted string for injection into the research task, or "" if no history.
    """
    pairs: list[str] = []
    i = 0
    while i < len(messages) - 1 and len(pairs) < limit:
        if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
            topic_snippet = messages[i]["content"][:200]
            pairs.append(f"- Prior topic: {topic_snippet}")
            i += 2
        else:
            i += 1

    if not pairs:
        return ""

    return "Prior session context (for reference only — focus on the current topic):\n" + "\n".join(pairs)


@cl.on_chat_end
def on_chat_end():
    pass
