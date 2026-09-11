"""Shared LLM client — uses Groq (free, fast) with retry logic."""
import json
import re
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage

from app.core.logging import logger


def get_llm(temperature: float = 0.4):
    api_key = os.getenv("GROQ_API_KEY", "")
    return ChatGroq(
        model="gemma2-9b-it",
        temperature=temperature,
        groq_api_key=api_key,
        max_tokens=1024,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def invoke_llm(
    system_prompt: str,
    human_prompt: str,
    temperature: float = 0.4,
) -> str:
    llm = get_llm(temperature)
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]
    response = await llm.ainvoke(messages)
    return response.content


async def invoke_llm_json(
    system_prompt: str,
    human_prompt: str,
    temperature: float = 0.2,
) -> dict | list:
    raw = await invoke_llm(system_prompt, human_prompt, temperature)
    return parse_json_response(raw)


def parse_json_response(raw: str) -> dict | list:
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        logger.error("json_parse_failed", raw=raw[:300])
        raise ValueError(f"Could not parse JSON: {raw[:200]}")
