# Alias Tagging Support

## Overview

Add support for tagging image aliases (e.g., `dotnet:9.0.300` -> `dotnet:9`) using `crane tag`.

## Background

The `dist/` folder contains alias files - text files where the filename is the alias and the content is the target tag:
- `dist/dotnet/9` contains `9.0.300` (meaning `dotnet:9` -> `dotnet:9.0.300`)
- `dist/dotnet/9.0` contains `9.0.300`
- `dist/python/3.13` contains `3.13.7`

## Requirements

1. **Auto-tag during build**: After successful build, automatically apply aliases from dist/
2. **Retag command**: Explicit command to apply aliases to existing registry images
3. **Error handling**: For retag, return error if image doesn't exist in registry

## Implementation

### 1. get_aliases_for_tag() - building.py

```python
def get_aliases_for_tag(image_name: str, tag_name: str) -> list[str]:
    """Get all aliases that point to a specific tag."""
```

Scans `dist/<image>/` for alias files (non-directories) where content matches tag_name.

### 2. tag_aliases() - building.py

```python
def tag_aliases(image_ref: str, snapshot_id: str | None = None) -> int:
    """Apply all aliases for an image using crane tag."""
```

Uses `crane tag` to create additional tags for an existing registry image.

### 3. Integration into run_build()

Call `tag_aliases()` after successful build completes.

### 4. cmd_retag() - __main__.py

New command: `image-manager retag <image:tag> [--snapshot-id ID]`

- Validates image exists in registry using `crane digest`
- Applies all aliases using `tag_aliases()`
- Returns error if image not found

## Usage

```bash
# Build with auto-aliasing
image-manager build dotnet:9.0.300
# Creates: dotnet:9.0.300, dotnet:9.0, dotnet:9

# Retag existing image
image-manager retag dotnet:9.0.300
# Applies aliases to existing registry image

# With snapshot
image-manager retag dotnet:9.0.300 --snapshot-id mr-123
```
