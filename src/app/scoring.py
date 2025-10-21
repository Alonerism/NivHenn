"""Score normalization and aggregation utilities."""
from typing import Optional


def normalize_to_100(value: Optional[float], min_val: float = 0, max_val: float = 100) -> int:
    """
    Normalize a value to 1-100 scale.
    
    Args:
        value: Input value to normalize
        min_val: Minimum expected value
        max_val: Maximum expected value
    
    Returns:
        Integer score between 1 and 100
    """
    if value is None:
        return 50  # Neutral default
    
    # Clamp to range
    value = max(min_val, min(max_val, value))
    
    # Normalize to 0-100
    if max_val == min_val:
        normalized = 50
    else:
        normalized = ((value - min_val) / (max_val - min_val)) * 100
    
    # Clamp to 1-100 and round
    return max(1, min(100, round(normalized)))


def to_int_1_100(value: Optional[float]) -> int:
    """
    Convert any numeric value to integer in range 1-100.
    
    Args:
        value: Input value
    
    Returns:
        Integer clamped between 1 and 100
    """
    if value is None:
        return 50  # Neutral default
    
    try:
        score = int(round(value))
        return max(1, min(100, score))
    except (ValueError, TypeError):
        return 50


def weighted_overall(scores: dict[str, int], weights: dict[str, float]) -> int:
    """
    Calculate weighted average score.
    
    Args:
        scores: Dictionary of agent names to scores (1-100)
        weights: Dictionary of agent names to weights (sum to 1.0)
    
    Returns:
        Weighted average score as integer 1-100
    """
    if not scores:
        return 50
    
    total_score = 0.0
    total_weight = 0.0
    
    for agent_name, weight in weights.items():
        score = scores.get(agent_name, 50)  # Default to neutral 50 if missing
        total_score += score * weight
        total_weight += weight
    
    # Normalize if weights don't sum to 1.0
    if total_weight > 0:
        final_score = total_score / total_weight
    else:
        final_score = 50
    
    return to_int_1_100(final_score)


def clamp_score(score: int, min_val: int = 1, max_val: int = 100) -> int:
    """
    Clamp score to valid range.
    
    Args:
        score: Input score
        min_val: Minimum allowed value (default 1)
        max_val: Maximum allowed value (default 100)
    
    Returns:
        Clamped integer score
    """
    return max(min_val, min(max_val, score))


def calculate_confidence(scores: dict[str, int]) -> str:
    """
    Calculate confidence level based on score variance.
    
    Args:
        scores: Dictionary of agent scores
    
    Returns:
        Confidence level: "High", "Medium", or "Low"
    """
    if not scores:
        return "Low"
    
    values = list(scores.values())
    if len(values) < 2:
        return "Low"
    
    # Calculate standard deviation
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    # Classify confidence based on agreement
    if std_dev < 10:
        return "High"
    elif std_dev < 20:
        return "Medium"
    else:
        return "Low"
