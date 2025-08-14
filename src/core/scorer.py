# Instruction count scoring
# Scores execution results based on instruction count to maximize runtime execution

from typing import List, Dict, Any
from dataclasses import dataclass
import math

@dataclass
class Score:
    """Score for a candidate input"""
    raw_score: float
    normalized_score: float
    metric: str

class ResourceScorer:
    """Scores execution results based on instruction count"""

    def __init__(self, metrics: List[str] = None):
        # Only support instruction_count metric
        self.metrics = ["instruction_count"]
        self.score_history = []

    def score(self, execution_result, metric: str = "instruction_count") -> float:
        """Score an execution result based on instruction count"""
        # Always use instruction_count regardless of input metric
        metric = "instruction_count"
        
        if not execution_result.success and not execution_result.timeout:
            return 0.0

        raw_score = self._calculate_raw_score(execution_result, metric)
        normalized_score = self._normalize_score(raw_score, metric)

        # Store for normalization history
        self.score_history.append({
            'metric': metric,
            'raw_score': raw_score,
            'normalized_score': normalized_score
        })

        return normalized_score

    def _calculate_raw_score(self, result, metric: str) -> float:
        """Calculate raw score based on instruction count"""
        return float(result.instruction_count)

    def _normalize_score(self, raw_score: float, metric: str) -> float:
        """Normalize score relative to historical performance"""
        if len(self.score_history) < 2:
            return raw_score

        # Get historical scores for this metric
        historical_scores = [
            entry['raw_score'] for entry in self.score_history
            if entry['metric'] == metric
        ]

        if not historical_scores:
            return raw_score

        # Normalize using min-max scaling
        min_score = min(historical_scores)
        max_score = max(historical_scores)

        if max_score == min_score:
            return 1.0

        normalized = (raw_score - min_score) / (max_score - min_score)
        return max(0.0, min(1.0, normalized))
