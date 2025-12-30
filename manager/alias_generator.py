import re
from manager.models import Tag


SEMVER_PATTERN = re.compile(r'^v?(\d+)\.(\d+)\.(\d+).*$')


def parse_semver(tag_name: str) -> tuple[int, int, int] | None:
    """
    Parse semantic version from tag name.

    Returns (major, minor, patch) tuple or None if not semver.
    Allows optional 'v' prefix and ignores any suffix after version.

    Examples:
        "9.0.100" → (9, 0, 100)
        "v9.0.100" → (9, 0, 100)
        "3.13.7-beta" → (3, 13, 7)
        "latest" → None
    """
    match = SEMVER_PATTERN.match(tag_name)
    if not match:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def generate_semver_aliases(tags: list[Tag]) -> dict[str, str]:
    """
    Generate automatic semver aliases from tags.

    For each semver tag, generates aliases for:
    - Major version (e.g., "9" → highest 9.x.x)
    - Major.minor version (e.g., "9.0" → highest 9.0.x)

    Non-semver tags are silently skipped.

    Args:
        tags: List of Tag objects to analyze

    Returns:
        Dict mapping alias names to tag names

    Example:
        Tags: ["9.0.100", "9.0.200", "9.1.50"]
        Returns: {"9": "9.1.50", "9.0": "9.0.200", "9.1": "9.1.50"}
    """
    # Step 1: Parse tags into (version_tuple, tag_name, suffix) tuples
    parsed_tags = []
    for tag in tags:
        version = parse_semver(tag.name)
        if version:
            # Extract suffix from tag name
            major, minor, patch = version
            # Build the version string, accounting for optional 'v' prefix
            tag_lower = tag.name
            has_v = tag_lower.startswith('v')
            version_str = f"{major}.{minor}.{patch}"

            # Find where version ends in the tag name
            if has_v:
                search_str = f"v{version_str}"
            else:
                search_str = version_str

            idx = tag.name.find(search_str)
            if idx >= 0:
                suffix = tag.name[idx + len(search_str):]
            else:
                suffix = ""

            parsed_tags.append((version, tag.name, suffix))

    if not parsed_tags:
        return {}  # No semver tags found

    # Step 2: Group by prefixes (including suffix)
    groups = {}
    for (major, minor, patch), tag_name, suffix in parsed_tags:
        # Major alias: "9" or "9-semantic" → highest 9.x.x
        major_key = f"{major}{suffix}"
        # Major.minor alias: "9.0" or "9.0-semantic" → highest 9.0.x
        minor_key = f"{major}.{minor}{suffix}"

        if major_key not in groups:
            groups[major_key] = []
        groups[major_key].append(((major, minor, patch), tag_name))

        if minor_key not in groups:
            groups[minor_key] = []
        groups[minor_key].append(((major, minor, patch), tag_name))

    # Step 3: Find highest in each group
    aliases = {}
    for prefix, versions in groups.items():
        # Sort by version tuple (lexicographic), take highest
        highest = max(versions, key=lambda x: x[0])
        aliases[prefix] = highest[1]  # tag_name

    return aliases
