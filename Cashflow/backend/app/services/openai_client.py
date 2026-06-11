from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import structlog
from openai import APIError, OpenAI

from app.config import get_settings
from app.services.currency_format import INR_OUTPUT_RULES, format_context_for_llm, normalize_inr_in_narrative

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = f"""You are a treasury and cashflow advisory assistant for a corporate finance team.
Use ONLY the financial context provided. Cite specific numbers from the data.
{INR_OUTPUT_RULES}
Write in clear, professional prose with short headings and bullet points where helpful.
Do not invent figures, months, or recommendations that are not supported by the context.
If the context is insufficient, say what is missing."""


def _get_client() -> OpenAI:
    settings = get_settings()
    kwargs: Dict[str, Any] = {
        "api_key": settings.openai_api_key,
        "timeout": settings.openai_timeout_seconds,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def is_available() -> bool:
    settings = get_settings()
    return settings.llm_enabled and bool(settings.openai_api_key.strip())


def list_models() -> List[str]:
    if not is_available():
        return []
    return [get_settings().openai_model]


def resolve_model() -> str:
    return get_settings().openai_model


def chat(
    user_prompt: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.llm_enabled:
        return {
            "narrative": None,
            "model": None,
            "available": False,
            "error": "LLM is disabled (LLM_ENABLED=false).",
        }
    if not settings.openai_api_key.strip():
        return {
            "narrative": None,
            "model": None,
            "available": False,
            "error": "OpenAI API key is not configured (OPENAI_API_KEY).",
        }

    selected_model = model or resolve_model()
    context_block = ""
    if context is not None:
        llm_context = {
            "currency": "INR (Indian Rupees)",
            "formatting": INR_OUTPUT_RULES,
            "data": format_context_for_llm(context),
        }
        context_block = (
            "\n\nTreasury data context (JSON):\n"
            f"{json.dumps(llm_context, indent=2, default=str)}"
        )

    try:
        response = _get_client().chat.completions.create(
            model=selected_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"{user_prompt}{context_block}"},
            ],
            temperature=0.3,
        )
        narrative = (response.choices[0].message.content or "").strip()
        narrative = normalize_inr_in_narrative(narrative)
        return {
            "narrative": narrative or None,
            "model": response.model or selected_model,
            "available": True,
            "error": None,
        }
    except APIError as exc:
        logger.warning("openai_chat_failed", error=str(exc), model=selected_model)
        return {
            "narrative": None,
            "model": selected_model,
            "available": False,
            "error": f"OpenAI request failed: {exc}",
        }
    except Exception as exc:
        logger.warning("openai_chat_failed", error=str(exc), model=selected_model)
        return {
            "narrative": None,
            "model": selected_model,
            "available": False,
            "error": f"OpenAI request failed: {exc}",
        }
