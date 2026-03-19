"""
engine/ai_bot.py — Real AI bot integration for BYTE Wars.

Replaces MockBot with actual AI API calls. Supports any OpenAI-compatible
endpoint (Claude, GPT, Gemini, etc.) via the OpenAI Python SDK format.

Flow:
1. Receives game_state with full battle context
2. Builds a prompt from the champion's system_prompt + game_state.to_prompt()
3. Calls the AI model via HTTP (OpenAI-compatible chat completions)
4. Parses the JSON response into action dicts
5. Falls back to random actions if the API call fails or times out

Core rule #7: Platform-agnostic AI — supports any OpenAI-compatible endpoint.
"""

import asyncio
import json
import random
import httpx

from engine.turn_manager import MAX_ACTION_POINTS


# Timeout for AI API calls (seconds). If exceeded, random fallback is used.
AI_TIMEOUT_SECONDS = 10

# Map model prefixes to their API base URLs
MODEL_ENDPOINTS = {
    "claude": "https://api.anthropic.com/v1",
    "gpt": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
}

# Default base URL if model prefix isn't recognized
DEFAULT_ENDPOINT = "https://api.openai.com/v1"


def _get_base_url(model: str) -> str:
    """Determine the API base URL based on the model name prefix."""
    for prefix, url in MODEL_ENDPOINTS.items():
        if model.startswith(prefix):
            return url
    return DEFAULT_ENDPOINT


def _build_headers(api_key: str, model: str) -> dict:
    """Build request headers based on the provider."""
    if model.startswith("claude"):
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _build_request_body(system_prompt: str, user_prompt: str, model: str) -> dict:
    """Build the chat completions request body."""
    if model.startswith("claude"):
        # Anthropic Messages API format
        return {
            "model": model,
            "max_tokens": 512,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
    # OpenAI-compatible format (GPT, Gemini, etc.)
    return {
        "model": model,
        "max_tokens": 512,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }


def _parse_response_body(response_json: dict, model: str) -> str:
    """Extract the text content from the API response."""
    if model.startswith("claude"):
        # Anthropic format: {"content": [{"type": "text", "text": "..."}]}
        content = response_json.get("content", [])
        if content and isinstance(content, list):
            return content[0].get("text", "")
        return ""
    # OpenAI format: {"choices": [{"message": {"content": "..."}}]}
    choices = response_json.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _extract_json_from_text(text: str) -> list[dict] | None:
    """
    Extract a JSON array from AI response text.

    AI models often wrap JSON in markdown code blocks or include
    explanatory text. This function handles common patterns.
    """
    # Try direct parse first
    text = text.strip()
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    if "```" in text:
        blocks = text.split("```")
        for block in blocks:
            block = block.strip()
            if block.startswith("json"):
                block = block[4:].strip()
            try:
                result = json.loads(block)
                if isinstance(result, list):
                    return result
            except json.JSONDecodeError:
                continue

    # Try finding array in the text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start:end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return None


class AIBot:
    """
    AI-powered bot that calls real LLM APIs for action selection.

    Supports Claude, GPT, Gemini, and any OpenAI-compatible endpoint.
    Falls back to random action selection if the API call fails.
    """

    def __init__(self, api_key: str, model: str, system_prompt: str = ""):
        """
        Args:
            api_key: Decrypted API key for the AI provider.
            model: Model identifier (e.g., "claude-sonnet-4-6", "gpt-4o").
            system_prompt: Champion's custom strategy prompt.
        """
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt or (
            "You are an AI champion in a battle arena. "
            "Choose actions strategically to defeat your opponents. "
            "Respond ONLY with a JSON array of actions."
        )

    async def choose_actions_async(
        self,
        champion,
        opponents: list,
        available_actions: dict,
        game_state=None,
    ) -> list[dict]:
        """
        Call the AI model to choose actions for this turn.

        Args:
            champion: BattleChampion whose turn it is.
            opponents: List of opponent BattleChampions.
            available_actions: Dict of all available actions.
            game_state: GameState object with full battle context.

        Returns:
            List of action dicts with 'action' and 'target_id' keys.
        """
        if game_state is None:
            return self._random_fallback(champion, opponents, available_actions)

        user_prompt = game_state.to_prompt()

        try:
            base_url = _get_base_url(self.model)
            headers = _build_headers(self.api_key, self.model)

            if self.model.startswith("claude"):
                url = f"{base_url}/messages"
            else:
                url = f"{base_url}/chat/completions"

            body = _build_request_body(self.system_prompt, user_prompt, self.model)

            async with httpx.AsyncClient(timeout=AI_TIMEOUT_SECONDS) as client:
                resp = await client.post(url, headers=headers, json=body)
                resp.raise_for_status()
                response_json = resp.json()

            text = _parse_response_body(response_json, self.model)
            actions = _extract_json_from_text(text)

            if actions:
                return actions

        except (httpx.TimeoutException, httpx.HTTPStatusError, Exception):
            # API failed or timed out — use random fallback
            pass

        return self._random_fallback(champion, opponents, available_actions)

    def choose_actions(
        self,
        champion,
        opponents: list,
        available_actions: dict,
        game_state=None,
    ) -> list[dict]:
        """
        Synchronous wrapper for choose_actions_async.

        Used by the battle engine which currently runs synchronously.
        Tries to use an existing event loop, or creates a new one.
        """
        try:
            loop = asyncio.get_running_loop()
            # We're inside an async context — schedule as a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = loop.run_in_executor(
                    pool,
                    lambda: asyncio.run(
                        self.choose_actions_async(
                            champion, opponents, available_actions, game_state
                        )
                    ),
                )
                # This is a coroutine, return fallback for now
                return self._random_fallback(champion, opponents, available_actions)
        except RuntimeError:
            # No event loop — safe to use asyncio.run
            return asyncio.run(
                self.choose_actions_async(
                    champion, opponents, available_actions, game_state
                )
            )

    def _random_fallback(
        self,
        champion,
        opponents: list,
        available_actions: dict,
    ) -> list[dict]:
        """
        Random action selection fallback when AI API is unavailable.

        Same logic as MockBot — randomly picks affordable actions up to
        the 3 AP budget.
        """
        chosen = []
        remaining_ap = MAX_ACTION_POINTS

        while remaining_ap > 0:
            affordable = [
                a for a in available_actions.values()
                if a["action_point_cost"] <= remaining_ap
            ]
            if not affordable:
                break

            action = random.choice(affordable)
            action_entry = {"action": action["name"]}

            if action["target"] == "single_enemy":
                living = [o for o in opponents if o.is_alive]
                if not living:
                    break
                action_entry["target_id"] = random.choice(living).id
            elif action["target"] == "self":
                action_entry["target_id"] = champion.id

            chosen.append(action_entry)
            remaining_ap -= action["action_point_cost"]

        return chosen
