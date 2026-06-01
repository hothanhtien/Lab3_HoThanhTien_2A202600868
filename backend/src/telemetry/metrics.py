from typing import Dict, Any
from src.telemetry.logger import logger

# Real pricing per 1K tokens
PRICING = {
    "gpt-4o":           {"prompt": 0.005,    "completion": 0.015},
    "gpt-4o-mini":      {"prompt": 0.00015,  "completion": 0.0006},
    "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.0003},
}

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    Kế thừa từ Lab3 skeleton, bổ sung real pricing logic.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """Logs a single request metric to our telemetry."""
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_usd": self._calculate_cost(model, usage),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)
        return metric

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Real pricing logic based on model."""
        pricing = PRICING.get(model, {"prompt": 0.01, "completion": 0.03})
        prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing["prompt"]
        completion_cost = (usage.get("completion_tokens", 0) / 1000) * pricing["completion"]
        return round(prompt_cost + completion_cost, 6)

# Global tracker instance
tracker = PerformanceTracker()
