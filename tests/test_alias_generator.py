from manager.alias_generator import parse_semver, generate_semver_aliases
from manager.models import Tag


def test_parse_semver_basic():
    """Test basic semver parsing"""
    assert parse_semver("9.0.100") == (9, 0, 100)
    assert parse_semver("3.13.7") == (3, 13, 7)


def test_parse_semver_with_v_prefix():
    """Test parsing with v prefix"""
    assert parse_semver("v9.0.100") == (9, 0, 100)
    assert parse_semver("v1.2.3") == (1, 2, 3)


def test_parse_semver_with_suffix():
    """Test parsing tags with build metadata"""
    assert parse_semver("9.0.100-beta") == (9, 0, 100)
    assert parse_semver("1.2.3-rc.1") == (1, 2, 3)
    assert parse_semver("v1.2.3-alpha+build.123") == (1, 2, 3)


def test_parse_semver_invalid():
    """Test that non-semver tags return None"""
    assert parse_semver("latest") is None
    assert parse_semver("stable") is None
    assert parse_semver("1.2") is None  # Missing patch
    assert parse_semver("edge") is None


def test_generate_aliases_simple():
    """Test alias generation from simple tags"""
    tags = [
        Tag("9.0.100", {}, {}),
        Tag("9.0.200", {}, {})
    ]
    aliases = generate_semver_aliases(tags)

    assert aliases == {
        "9": "9.0.200",
        "9.0": "9.0.200"
    }


def test_generate_aliases_multiple_minors():
    """Test with multiple minor versions"""
    tags = [
        Tag("9.0.100", {}, {}),
        Tag("9.0.200", {}, {}),
        Tag("9.1.50", {}, {})
    ]
    aliases = generate_semver_aliases(tags)

    assert aliases == {
        "9": "9.1.50",      # Highest 9.x.x
        "9.0": "9.0.200",   # Highest 9.0.x
        "9.1": "9.1.50"     # Highest 9.1.x
    }


def test_generate_aliases_multiple_majors():
    """Test with major version jump"""
    tags = [
        Tag("9.0.100", {}, {}),
        Tag("10.0.0", {}, {})
    ]
    aliases = generate_semver_aliases(tags)

    assert aliases == {
        "9": "9.0.100",
        "9.0": "9.0.100",
        "10": "10.0.0",
        "10.0": "10.0.0"
    }


def test_generate_aliases_skips_non_semver():
    """Test that non-semver tags are silently skipped"""
    tags = [
        Tag("9.0.100", {}, {}),
        Tag("latest", {}, {}),
        Tag("stable", {}, {})
    ]
    aliases = generate_semver_aliases(tags)

    assert aliases == {"9": "9.0.100", "9.0": "9.0.100"}


def test_generate_aliases_empty():
    """Test with no semver tags"""
    tags = [Tag("latest", {}, {}), Tag("stable", {}, {})]
    aliases = generate_semver_aliases(tags)

    assert aliases == {}


def test_generate_aliases_variant_tags():
    """Test alias generation for variant tags with suffix"""
    tags = [
        Tag("9.0.100-semantic", {}, {}),
        Tag("9.0.200-semantic", {}, {})
    ]
    aliases = generate_semver_aliases(tags)

    assert aliases == {
        "9-semantic": "9.0.200-semantic",
        "9.0-semantic": "9.0.200-semantic"
    }
