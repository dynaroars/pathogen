# Input selection strategies
# Implements evolutionary selection algorithms to choose the best inputs for the next generation

from typing import List, Tuple, Dict, Any
import random
import math

class InputSelector:
    """Selects best inputs for next generation"""

    def __init__(self, config: Dict[str, Any]):
        self.elite_size = config.get('elite_size', 3)
        self.mutation_rate = config.get('mutation_rate', 0.3)
        self.crossover_rate = config.get('crossover_rate', 0.7)

    def select_best(self, current_results: List[Tuple[str, float]],
                   previous_best: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        """Select best inputs from current and previous generations"""

        # Combine current and previous results
        all_candidates = current_results + previous_best

        # Remove duplicates (keep highest score)
        unique_candidates = {}
        for input_data, score in all_candidates:
            if input_data not in unique_candidates or score > unique_candidates[input_data]:
                unique_candidates[input_data] = score

        # Convert back to list and sort by score
        sorted_candidates = [(input_data, score) for input_data, score in unique_candidates.items()]
        sorted_candidates.sort(key=lambda x: x[1], reverse=True)

        # Select elite individuals
        elite = sorted_candidates[:self.elite_size]

        # Tournament selection for remaining slots
        remaining_slots = max(0, len(current_results) - self.elite_size)
        if remaining_slots > 0:
            tournament_selected = self._tournament_selection(
                sorted_candidates[self.elite_size:],
                remaining_slots
            )
            elite.extend(tournament_selected)

        return elite

    def _tournament_selection(self, candidates: List[Tuple[str, float]],
                            num_select: int, tournament_size: int = 3) -> List[Tuple[str, float]]:
        """Tournament selection for genetic algorithm"""
        selected = []

        for _ in range(num_select):
            # Randomly select candidates for tournament
            tournament = random.sample(candidates, min(tournament_size, len(candidates)))

            # Select winner (highest score)
            winner = max(tournament, key=lambda x: x[1])
            selected.append(winner)

        return selected
