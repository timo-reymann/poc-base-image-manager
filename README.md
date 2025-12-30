Proof of Concept for (CI) image management
===

Proof of concept for easy (CI) image management, which is also transferable to any kind of prebuilt images provided;
e.g. runtime images.

## Requirements

- Docker 
- uv
- Python 3.13
- [container-structure-test](https://github.com/GoogleContainerTools/container-structure-test)

## Usage

- `uv install`
- `uv run image-manager`
- Inspect generated files in dist/
    - Folders for builds
    - Files for tags (would be `crane tag` or similar)

## Example

Showcase on how the images could be built and tested.

1. Generate the files
    ```shell
    uv run image-manager
    ```
1. Build the base image
   ```shell
   docker build dist/base/2025.09/ -f dist/base/2025.09/Dockerfile  -t base:2025.9
   ```
2. Run tests for the built image
    ```shell
    container-structure-test test --image base:2025.09 --config dist/base/2025.09/test.yml
    ```
3. Build dotnet 9.0.300 which uses the base image
    ```shell
    docker build dist/dotnet/9.0.300 -f dist/dotnet/9.0.300/Dockerfile  -t dotnet:9.0.30
    ```
4. Run tests for built dotnet image
    ```shell
    container-structure-test test --image dotnet:9.0.300 --config dist/dotnet/9.0.300/test.ym
    ```

## Features

- Uses yaml and subfolders by convention to create images
- Create matrix of variants and tags for each image
- Supports layering images via variants
- Allows supporting multiple tag hierarchies
- **Automatic semantic version aliases** - Generates all prefix-level aliases from tags
- Integration with container-structure-test for testing containers

## Missing features

- Specify registry
- CI Generation or directly building images
- More intelligent version parsing and sorting (potentially via strategy that can be specified)

## Implementation

- **Three-layer architecture**: Config → Model → Rendering
- **Config layer**: Pydantic models for YAML validation
- **Model layer**: Business logic for merging and resolution
- **Rendering layer**: Jinja2 template generation
- **Smart template discovery**: Convention with explicit overrides
- **Variable merging**: Override cascade from image → tag → variant
- **Variant tags**: Automatic generation with suffix-based naming

See [docs/architecture.md](docs/architecture.md) for details.