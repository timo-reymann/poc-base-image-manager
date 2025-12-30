from pathlib import Path
from manager.models import Image, Tag, Variant


def test_tag_with_merged_data():
    """Test Tag stores merged versions and variables"""
    tag = Tag(
        name="3.13.7",
        versions={"python": "3.13.7", "uv": "0.8.22"},
        variables={"ENV": "production", "DEBUG": "false"}
    )

    assert tag.name == "3.13.7"
    assert tag.versions["python"] == "3.13.7"
    assert tag.variables["ENV"] == "production"


def test_variant_with_generated_tags():
    """Test Variant stores generated tags"""
    tag1 = Tag(name="3.13.7-browser", versions={}, variables={})
    tag2 = Tag(name="3.13.6-browser", versions={}, variables={})

    variant = Variant(
        name="browser",
        template_path=Path("/fake/Dockerfile.browser.tmpl"),
        tags=[tag1, tag2]
    )

    assert variant.name == "browser"
    assert len(variant.tags) == 2
    assert variant.tags[0].name == "3.13.7-browser"
    assert variant.template_path == Path("/fake/Dockerfile.browser.tmpl")


def test_image_with_tags_and_variants():
    """Test Image stores resolved data"""
    tag = Tag(name="3.13.7", versions={}, variables={})
    variant = Variant(
        name="browser",
        template_path=Path("/fake/Dockerfile.tmpl"),
        tags=[]
    )

    image = Image(
        name="python",
        path=Path("/fake/images/python/3"),
        template_path=Path("/fake/Dockerfile.tmpl"),
        versions={"uv": "0.8.22"},
        variables={"ENV": "production"},
        tags=[tag],
        variants=[variant],
        is_base_image=False,
        extends=None,
        aliases={}
    )

    assert image.name == "python"
    assert len(image.tags) == 1
    assert len(image.variants) == 1
    assert image.versions["uv"] == "0.8.22"


def test_variant_with_aliases():
    """Test Variant stores aliases dict"""
    tag1 = Tag(name="9.0.100-browser", versions={}, variables={})

    variant = Variant(
        name="browser",
        template_path=Path("/fake/Dockerfile.browser.tpl"),
        tags=[tag1],
        aliases={"9-browser": "9.0.100-browser"}
    )

    assert variant.aliases == {"9-browser": "9.0.100-browser"}
