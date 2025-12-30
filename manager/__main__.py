import os
import shutil
import sys
from pathlib import Path

from manager.config import ConfigLoader
from manager.models import ModelResolver
from manager.rendering import RenderContext, render_dockerfile, render_test_config
from manager.dependency_graph import sort_images, extract_dependencies, CyclicDependencyError


def main():
    dist_path = Path("dist")
    shutil.rmtree(dist_path.__str__(), ignore_errors=True)

    # Load and resolve all images
    resolver = ModelResolver()
    all_images = []
    for image_yaml in Path("images").glob("**/image.yml"):
        config = ConfigLoader.load(image_yaml)
        image = resolver.resolve(config, image_yaml.parent)
        all_images.append(image)

    # Sort images by dependencies to ensure correct build order
    try:
        sorted_images = sort_images(all_images)
    except CyclicDependencyError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nCannot generate images due to circular dependencies.", file=sys.stderr)
        print("Please review your image configurations and remove any circular references.", file=sys.stderr)
        sys.exit(1)

    # Log the build order with dependencies
    print("Build order (dependencies resolved):")
    dependencies = extract_dependencies(all_images)
    for i, image in enumerate(sorted_images, 1):
        deps = dependencies.get(image.name, set())
        if deps:
            deps_str = ", ".join(sorted(deps))
            print(f"  {i}. {image.name} (depends on: {deps_str})")
        else:
            print(f"  {i}. {image.name} (no dependencies)")
    print()

    for image in sorted_images:
        image_out_path = dist_path.joinpath(image.name)

        # Render base tags
        for tag in image.tags:
            tag_out_path = image_out_path.joinpath(tag.name)
            tag_out_path.mkdir(parents=True, exist_ok=True)

            ctx = RenderContext(image=image, all=sorted_images, tag=tag, variant=None)

            rendered_dockerfile = render_dockerfile(ctx)
            tag_out_path.joinpath("Dockerfile").write_text(rendered_dockerfile)

            rendered_test_config = render_test_config(ctx)
            tag_out_path.joinpath("test.yml").write_text(rendered_test_config)

        # Render variant tags
        for variant in image.variants:
            for variant_tag in variant.tags:
                variant_out_path = image_out_path.joinpath(variant_tag.name)
                variant_out_path.mkdir(parents=True, exist_ok=True)

                ctx = RenderContext(image=image, all=sorted_images, tag=variant_tag, variant=variant)

                rendered_dockerfile = render_dockerfile(ctx)
                variant_out_path.joinpath("Dockerfile").write_text(rendered_dockerfile)
                rendered_test_config = render_test_config(ctx)

                variant_out_path.joinpath("test.yml").write_text(rendered_test_config)

        # Write base aliases
        for alias, tag_name in image.aliases.items():
            alias_out_path = image_out_path.joinpath(alias)
            alias_out_path.write_text(tag_name)

        # Write variant aliases
        for variant in image.variants:
            for alias, tag_name in variant.aliases.items():
                alias_out_path = image_out_path.joinpath(alias)
                alias_out_path.write_text(tag_name)


if __name__ == "__main__":
    main()
