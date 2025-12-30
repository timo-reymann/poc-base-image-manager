class Merger:
    """Merges dictionaries with override semantics"""

    @staticmethod
    def merge(*dicts: dict[str, str]) -> dict[str, str]:
        """
        Merge multiple dicts with override cascade.
        Later dicts override earlier ones on key conflicts.

        Example:
            merge({"a": "1"}, {"a": "2"}) -> {"a": "2"}
        """
        result = {}
        for d in dicts:
            result |= d
        return result
