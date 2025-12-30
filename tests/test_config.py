from pathlib import Path
from manager.config import ImageConfig, TagConfig, VariantConfig, ConfigLoader


def test_load_minimal_config(tmp_path):
    """Test loading a minimal valid config"""
    config_file = tmp_path / "image.yml"
    config_file.write_text("""
name: test-image
tags:
  - name: "1.0"
""")

    config = ConfigLoader.load(config_file)
    assert config.name == "test-image"
    assert len(config.tags) == 1
    assert config.tags[0].name == "1.0"


def test_load_config_with_variants(tmp_path):
    """Test loading config with variants"""
    config_file = tmp_path / "image.yml"
    config_file.write_text("""
name: python
versions:
  uv: "0.8.22"
variables:
  ENV: "production"
tags:
  - name: "3.13.7"
    versions:
      python: "3.13.7"
variants:
  - name: browser
    tag_suffix: "-browser"
    versions:
      chromium: "120.0"
""")

    config = ConfigLoader.load(config_file)
    assert config.name == "python"
    assert config.versions == {"uv": "0.8.22"}
    assert config.variables == {"ENV": "production"}
    assert len(config.variants) == 1
    assert config.variants[0].name == "browser"
    assert config.variants[0].tag_suffix == "-browser"


def test_tag_config_defaults():
    """Test TagConfig has sensible defaults"""
    tag = TagConfig(name="1.0")
    assert tag.name == "1.0"
    assert tag.versions == {}
    assert tag.variables == {}


def test_variant_config_requires_suffix():
    """Test VariantConfig requires tag_suffix"""
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        VariantConfig(name="browser")  # Missing tag_suffix
