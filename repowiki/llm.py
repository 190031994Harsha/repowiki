"""LLM client: OpenAI-compatible (OpenRouter, local proxies) or Anthropic.

Every call is logged to the run's trajectory (prompt, response, tokens, cost, latency).
Provider/model come from env or explicit args; nothing is hard-coded.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

# rough USD per 1M tokens (input, output); only for reporting, not billing truth
PRICES = {
    "deepseek/deepseek-chat-v3-0324": (0.27, 1.10),
    "moonshotai/kimi-k2": (0.57, 2.30),
    "anthropic/claude-sonnet-4.5": (3.00, 15.00),
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
}


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_s: float
    error: str = ""


class LLM:
    def __init__(self, model: str | None = None, trajectory=None):
        self.model = model or os.environ.get("REPOWIKI_MODEL", "deepseek/deepseek-chat-v3-0324")
        self.provider = os.environ.get("REPOWIKI_PROVIDER", "openrouter")
        self.trajectory = trajectory
        self.calls = 0
        self.total_cost = 0.0
        self.total_input = 0
        self.total_output = 0
        if self.provider == "openrouter":
            from openai import OpenAI
            self._client = OpenAI(
                base_url=os.environ.get("REPOWIKI_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=os.environ.get("OPENROUTER_API_KEY", ""))
            self._mode = "openai"
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic()
            self._mode = "anthropic"
        else:
            raise ValueError(f"unknown provider {self.provider}")

    def chat(self, system: str, user: str, max_tokens: int = 4096,
             temperature: float = 0.0, purpose: str = "") -> LLMResponse:
        """One LLM call with retry; logged to trajectory."""
        t0 = time.time()
        err = ""
        for attempt in range(3):
            try:
                if self._mode == "openai":
                    r = self._client.chat.completions.create(
                        model=self.model, temperature=temperature, max_tokens=max_tokens,
                        messages=[{"role": "system", "content": system},
                                  {"role": "user", "content": user}])
                    text = r.choices[0].message.content or ""
                    itok = r.usage.prompt_tokens if r.usage else 0
                    otok = r.usage.completion_tokens if r.usage else 0
                else:
                    r = self._client.messages.create(
                        model=self.model, max_tokens=max_tokens, temperature=temperature,
                        system=system,
                        messages=[{"role": "user", "content": user}])
                    text = "".join(b.text for b in r.content if b.type == "text")
                    itok, otok = r.usage.input_tokens, r.usage.output_tokens
                lat = time.time() - t0
                p_in, p_out = PRICES.get(self.model, (0.0, 0.0))
                cost = itok * p_in / 1e6 + otok * p_out / 1e6
                resp = LLMResponse(text=text, model=self.model, input_tokens=itok,
                                   output_tokens=otok, cost_usd=cost, latency_s=round(lat, 2))
                self._record(purpose, system, user, resp, attempt)
                return resp
            except Exception as e:
                err = repr(e)
                time.sleep(2 ** attempt)
        resp = LLMResponse(text="", model=self.model, input_tokens=0, output_tokens=0,
                           cost_usd=0.0, latency_s=round(time.time() - t0, 2), error=err)
        self._record(purpose, system, user, resp, 3)
        return resp

    def _record(self, purpose, system, user, resp: LLMResponse, attempt: int):
        self.calls += 1
        self.total_cost += resp.cost_usd
        self.total_input += resp.input_tokens
        self.total_output += resp.output_tokens
        if self.trajectory:
            self.trajectory.event("llm_call", {
                "purpose": purpose, "model": self.model, "attempt": attempt,
                "system": system, "user": user[:6000], "response": resp.text[:6000],
                "input_tokens": resp.input_tokens, "output_tokens": resp.output_tokens,
                "cost_usd": round(resp.cost_usd, 5), "latency_s": resp.latency_s,
                "error": resp.error,
            })
