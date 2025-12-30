# Architecture

## Overview

The image manager uses a three-layer architecture:

**Config Layer** → **Model Layer** → **Rendering Layer**

### Config Layer (`manager/config.py`)

Loads and validates YAML files using Pydantic:
- `ImageConfig` - Root configuration
- `TagConfig` - Individual tag config
- `VariantConfig` - Variant config
- `ConfigLoader` - YAML loader

No business logic - just validation and parsing.

### Model Layer (`manager/models.py`)

Transforms configs into resolved domain models:
- `Image` - Fully resolved image with computed data
- `Tag` - Tag with merged versions/variables
- `Variant` - Variant with generated tags
- `ModelResolver` - Transformation engine

This layer handles:
- Template resolution (explicit → variant → default)
- Version/variable merging (image → tag → variant)
- Variant tag generation (base tags + suffix)

### Rendering Layer (`manager/rendering.py`)

Generates output files from resolved models:
- Receives complete data (no late binding)
- Renders Jinja2 templates
- Writes Dockerfiles and test configs

## Data Flow

```
image.yml → ConfigLoader → ImageConfig
                              ↓
                        ModelResolver
                              ↓
                           Image (with Tags and Variants)
                              ↓
                          Renderer
                              ↓
                      Dockerfile + test.yml
```

## Template Resolution

Discovery order:
1. Explicit template from config
2. Variant-specific: `Dockerfile.{variant}.tmpl`
3. Default: `Dockerfile.tmpl`

## Variable Merging

Override cascade (later wins):
- Image → Tag → Variant

Both `versions` and `variables` use same merging strategy.

## Variant Tags

Variants inherit ALL base tags and apply suffix:
- Base: `["3.13.7", "3.13.6"]`
- Variant "browser" with suffix "-browser"
- Result: `["3.13.7-browser", "3.13.6-browser"]`

Each variant tag has fully merged versions/variables.

## Automatic Alias Generation

The system automatically generates semantic version aliases without manual configuration.

### AliasGenerator (`manager/alias_generator.py`)

Parses tags, detects semantic versions, and generates prefix-level aliases:
- `parse_semver(tag_name)` - Extracts (major, minor, patch) from tag names
- `generate_semver_aliases(tags)` - Creates alias mappings

### Alias Generation Rules

For tags like `9.0.100`, `9.0.200`, `9.1.50`:
- Major alias: `9` → `9.1.50` (highest 9.x.x)
- Minor aliases: `9.0` → `9.0.200`, `9.1` → `9.1.50`

Non-semver tags (like `latest`) are silently skipped.

### Variant Aliases

Variants automatically get aliases with suffix:
- Variant tags: `9.0.100-semantic`, `9.0.200-semantic`
- Aliases: `9-semantic` → `9.0.200-semantic`, `9.0-semantic` → `9.0.200-semantic`

### Integration

ModelResolver calls `generate_semver_aliases()` after building tags.
Aliases are stored in `Image.aliases` and `Variant.aliases` dicts.

