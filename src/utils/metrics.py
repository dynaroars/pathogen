# Instruction count metrics collection
# Tracks and analyzes instruction count metrics throughout fuzzing campaigns

import time
import psutil
import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict

@dataclass
class ExecutionMetrics:
    """Metrics for a single execution focused on instruction count"""
    timestamp: float
    instruction_count: int
    success: bool
    input_hash: str = ""

@dataclass
class CampaignMetrics:
    """Metrics for entire fuzzing campaign"""
    start_time: float = field(default_factory=time.time)
    end_time: float = 0
    total_executions: int = 0
    successful_executions: int = 0
    best_score: float = 0
    convergence_generation: int = -1
    execution_history: List[ExecutionMetrics] = field(default_factory=list)
    generation_stats: Dict[int, Dict[str, Any]] = field(default_factory=lambda: defaultdict(dict))

class MetricsCollector:
    """Collects and analyzes performance metrics"""

    def __init__(self):
        self.campaign_metrics = CampaignMetrics()
        self.current_generation = 0

    def record_execution(self, execution_result, input_data: str) -> None:
        """Record metrics from an execution"""
        metrics = ExecutionMetrics(
            timestamp=time.time(),
            instruction_count=execution_result.instruction_count,
            success=execution_result.success,
            input_hash=str(hash(input_data))
        )

        self.campaign_metrics.execution_history.append(metrics)
        self.campaign_metrics.total_executions += 1

        if execution_result.success:
            self.campaign_metrics.successful_executions += 1

        # Update best score
        score = execution_result.instruction_count
        if score > self.campaign_metrics.best_score:
            self.campaign_metrics.best_score = score

    def start_generation(self, generation: int) -> None:
        """Mark the start of a new generation"""
        self.current_generation = generation
        self.campaign_metrics.generation_stats[generation]['start_time'] = time.time()

    def end_generation(self, generation: int, best_score: float, avg_score: float) -> None:
        """Mark the end of a generation"""
        gen_stats = self.campaign_metrics.generation_stats[generation]
        gen_stats['end_time'] = time.time()
        gen_stats['duration'] = gen_stats['end_time'] - gen_stats['start_time']
        gen_stats['best_score'] = best_score
        gen_stats['avg_score'] = avg_score

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.campaign_metrics.execution_history:
            return {}

        executions = self.campaign_metrics.execution_history
        successful = [e for e in executions if e.success]

        stats = {
            'total_executions': len(executions),
            'successful_executions': len(successful),
            'success_rate': len(successful) / len(executions) if executions else 0,
            'best_instruction_count': max(e.instruction_count for e in successful) if successful else 0,
            'avg_instruction_count': sum(e.instruction_count for e in successful) / len(successful) if successful else 0,
            'total_runtime': time.time() - self.campaign_metrics.start_time,
        }

        return stats
