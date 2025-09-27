# Heuristics to detect specific algebra mistakes (stubs to expand).
def sign_error(prev: str, cur: str) -> bool:
    return False


def moved_term_without_operation(prev: str, cur: str) -> bool:
    return False


def division_by_zero_risk(prev: str, cur: str) -> bool:
    return False
