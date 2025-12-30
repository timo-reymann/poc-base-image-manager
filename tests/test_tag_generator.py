from manager.tag_generator import TagGenerator
from manager.models import Tag
from manager.config import VariantConfig


def test_generate_variant_tags_simple():
    """Test generating variant tags with suffix"""
    base_tags = [
        Tag(name="3.13.7", versions={}, variables={}),
        Tag(name="3.13.6", versions={}, variables={}),
    ]
    variant_config = VariantConfig(
        name="browser", tag_suffix="-browser", versions={}, variables={}
    )

    result = TagGenerator.generate_variant_tags(
        base_tags=base_tags,
        variant=variant_config,
        image_versions={},
        image_variables={},
    )

    assert len(result) == 2
    assert result[0].name == "3.13.7-browser"
    assert result[1].name == "3.13.6-browser"


def test_generate_variant_tags_with_merged_versions():
    """Test variant tags have merged versions"""
    base_tags = [
        Tag(name="3.13.7", versions={"python": "3.13.7", "uv": "0.8.22"}, variables={})
    ]
    variant_config = VariantConfig(
        name="browser",
        tag_suffix="-browser",
        versions={"chromium": "120.0"},
        variables={},
    )

    result = TagGenerator.generate_variant_tags(
        base_tags=base_tags,
        variant=variant_config,
        image_versions={"uv": "0.8.22"},  # Will be in base tag already
        image_variables={},
    )

    assert result[0].versions == {
        "python": "3.13.7",
        "uv": "0.8.22",
        "chromium": "120.0",
    }


def test_generate_variant_tags_with_override():
    """Test variant can override base tag values"""
    base_tags = [Tag(name="3.13.7", versions={}, variables={"ENV": "production"})]
    variant_config = VariantConfig(
        name="browser",
        tag_suffix="-browser",
        versions={},
        variables={"ENV": "testing", "BROWSER": "chrome"},
    )

    result = TagGenerator.generate_variant_tags(
        base_tags=base_tags,
        variant=variant_config,
        image_versions={},
        image_variables={},
    )

    assert result[0].variables == {
        "ENV": "testing",  # Variant overrides base
        "BROWSER": "chrome",
    }
