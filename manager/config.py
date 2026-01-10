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


class RegistryConfig:
    """Configuration for a single registry."""

    def __init__(self, url: str, username: str | None = None, password: str | None = None, default: bool = False):
        self.url = url
        self.username = username
        self.password = password
        self.default = default

    def get_auth(self) -> tuple[str, str] | None:
        """Get (username, password) tuple if both are set, None otherwise."""
        if self.username is None or self.password is None:
            return None
        return (self.username, self.password)


def clear_config_cache() -> None:
    """Clear the config cache. Useful for testing."""
    global _config_cache
    _config_cache = None


def expand_env_vars(value: str | None) -> str | None:
    """Expand ${VAR} references in a string value.

    Supports:
    - Pure env var: ${VAR}
    - Multiple env vars: ${USER}:${PASS}
    - Mixed content: https://${HOST}:5000

    Returns None if the value is None or any referenced env var is undefined.
    """
    if value is None:
        return None

    if not value:
        return value

    # Find all ${VAR} patterns
    pattern = r'\$\{([^}]+)\}'
    matches = list(re.finditer(pattern, value))

    if not matches:
        # No env var pattern found, return as-is
        return value

    # Expand all env vars
    result = value
    for match in reversed(matches):  # Reverse to preserve positions during replacement
        var_name = match.group(1)
        env_value = os.environ.get(var_name)
        if env_value is None:
            # Undefined env var - return None
            return None
        result = result[:match.start()] + env_value + result[match.end():]

    return result


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
    """Get the URL of the default push registry.

    With multi-registry config, returns the one marked as default.
    Falls back to legacy single registry format or localhost:5050.
    """
    config = load_config()

    # Check new multi-registry format first
    registries = config.get("registries", [])
    if registries:
        # Find the default registry
        for reg in registries:
            if reg.get("default", False):
                url = expand_env_vars(reg.get("url"))
                if url:
                    return url
        # No default set, use first registry
        if registries:
            url = expand_env_vars(registries[0].get("url"))
            if url:
                return url
        return DEFAULT_REGISTRY

    # Fall back to legacy single registry format
    registry = config.get("registry", {})
    url = registry.get("url")

    if url is None:
        return DEFAULT_REGISTRY

    expanded = expand_env_vars(url)

    if expanded is None:
        return DEFAULT_REGISTRY

    return expanded


def get_registry_auth() -> tuple[str, str] | None:
    """Get registry authentication credentials for the default push registry.

    Returns (username, password) tuple if both are configured,
    None otherwise.
    """
    config = load_config()

    # Check new multi-registry format first
    registries = config.get("registries", [])
    if registries:
        for reg in registries:
            if reg.get("default", False):
                username = expand_env_vars(reg.get("username"))
                password = expand_env_vars(reg.get("password"))
                if username and password:
                    return (username, password)
        return None

    # Fall back to legacy single registry format
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


def get_registries() -> list[RegistryConfig]:
    """Get all configured registries.

    Returns list of RegistryConfig objects. Falls back to legacy single
    registry format if 'registries' key is not present.
    """
    config = load_config()

    # Check new multi-registry format
    registries_config = config.get("registries", [])
    if registries_config:
        result = []
        for reg in registries_config:
            url = expand_env_vars(reg.get("url"))
            if not url:
                continue
            username = expand_env_vars(reg.get("username"))
            password = expand_env_vars(reg.get("password"))
            default = reg.get("default", False)
            result.append(RegistryConfig(url, username, password, default))
        return result

    # Fall back to legacy single registry format
    registry = config.get("registry", {})
    url = expand_env_vars(registry.get("url"))
    if not url:
        url = DEFAULT_REGISTRY

    username = expand_env_vars(registry.get("username"))
    password = expand_env_vars(registry.get("password"))

    # Legacy format: single registry is always the default
    return [RegistryConfig(url, username, password, default=True)]


def get_push_registry() -> RegistryConfig:
    """Get the registry to push images to (marked as default).

    Returns the registry marked as default, or the first registry,
    or a localhost fallback.
    """
    registries = get_registries()

    if not registries:
        return RegistryConfig(DEFAULT_REGISTRY, default=True)

    # Find the one marked as default
    for reg in registries:
        if reg.default:
            return reg

    # If no default is set, use the first one
    return registries[0]


def get_registry_auth_for(registry_url: str) -> tuple[str, str] | None:
    """Get authentication credentials for a specific registry.

    Matches by URL prefix (e.g., 'ghcr.io' matches 'ghcr.io/myorg/myimage').

    Args:
        registry_url: The registry URL or image reference to match

    Returns:
        (username, password) tuple if found, None otherwise
    """
    registries = get_registries()

    for reg in registries:
        # Match by URL prefix
        if registry_url.startswith(reg.url) or reg.url.startswith(registry_url.split("/")[0]):
            return reg.get_auth()

    return None


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
