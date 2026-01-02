"""Configuration loading from .image-manager.yml."""

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as

_config_cache: dict | None = None

CONFIG_FILE = ".image-manager.yml"
DEFAULT_REGISTRY = "localhost:5050"


def clear_config_cache() -> None:
    """Clear the config cache. Useful for testing."""
    global _config_cache
    _config_cache = None


def expand_env_vars(value: str | None) -> str | None:
    """Expand ${VAR} references in a string value.

    Returns None if the value is None or contains an undefined env var.
    """
    if value is None:
        return None

    if not value:
        return value

    # Check if it's a pure env var reference like ${VAR}
    match = re.fullmatch(r'\$\{([^}]+)\}', value)
    if match:
        var_name = match.group(1)
        return os.environ.get(var_name)

    # No env var pattern found, return as-is
    return value


def load_config() -> dict:
    """Load .image-manager.yml from current directory.

    Returns empty dict if file doesn't exist or is empty.
    Result is cached for the duration of the process.
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    config_path = Path.cwd() / CONFIG_FILE

    if not config_path.exists():
        _config_cache = {}
        return _config_cache

    try:
        content = config_path.read_text()
        _config_cache = yaml.safe_load(content) or {}
    except Exception:
        _config_cache = {}

    return _config_cache


def get_registry_url() -> str:
    """Get registry URL from config or default to localhost:5050."""
    config = load_config()

    registry = config.get("registry", {})
    url = registry.get("url")

    if url is None:
        return DEFAULT_REGISTRY

    expanded = expand_env_vars(url)

    if expanded is None:
        return DEFAULT_REGISTRY

    return expanded


def get_registry_auth() -> tuple[str, str] | None:
    """Get registry authentication credentials.

    Returns (username, password) tuple if both are configured,
    None otherwise.
    """
    config = load_config()

    registry = config.get("registry", {})
    username = registry.get("username")
    password = registry.get("password")

    if username is None or password is None:
        return None

    expanded_username = expand_env_vars(username)
    expanded_password = expand_env_vars(password)

    if expanded_username is None or expanded_password is None:
        return None

    return (expanded_username, expanded_password)


class TagConfig(BaseModel):
    """Configuration for a single tag"""
    name: str
    versions: dict[str, str] = {}
    variables: dict[str, str] = {}
    rootfs_user: str | None = None
    rootfs_copy: bool | None = None


class VariantConfig(BaseModel):
    """Configuration for a variant"""
    name: str
    tag_suffix: str
    template: str | None = None
    versions: dict[str, str] = {}
    variables: dict[str, str] = {}
    rootfs_user: str | None = None
    rootfs_copy: bool | None = None


class ImageConfig(BaseModel):
    """Root configuration from image.yml"""
    name: str | None = None
    template: str | None = None
    versions: dict[str, str] = {}
    variables: dict[str, str] = {}
    tags: list[TagConfig]
    variants: list[VariantConfig] = []
    is_base_image: bool = False
    extends: str | None = None
    aliases: dict[str, str] = {}
    rootfs_user: str | None = None
    rootfs_copy: bool | None = None


class ConfigLoader:
    """Loads and validates image.yml files"""

    @staticmethod
    def load(path: Path) -> ImageConfig:
        """Load and validate an image.yml file"""
        return parse_yaml_file_as(ImageConfig, path)
