from manager.merger import Merger


def test_merge_two_dicts():
    """Test basic dict merging with override"""
    base = {"a": "1", "b": "2"}
    override = {"b": "3", "c": "4"}

    result = Merger.merge(base, override)

    assert result == {"a": "1", "b": "3", "c": "4"}


def test_merge_three_dicts():
    """Test three-level merge (image → tag → variant)"""
    image = {"uv": "0.8.22", "python": "3.13.0"}
    tag = {"python": "3.13.7", "pip": "23.1"}
    variant = {"chromium": "120.0"}

    result = Merger.merge(image, tag, variant)

    assert result == {
        "uv": "0.8.22",
        "python": "3.13.7",  # Tag overrides image
        "pip": "23.1",
        "chromium": "120.0"
    }


def test_merge_empty_dicts():
    """Test merging with empty dicts"""
    result = Merger.merge({}, {"a": "1"}, {})
    assert result == {"a": "1"}


def test_merge_single_dict():
    """Test merging single dict returns copy"""
    original = {"a": "1"}
    result = Merger.merge(original)

    assert result == original
    assert result is not original  # Should be a copy
