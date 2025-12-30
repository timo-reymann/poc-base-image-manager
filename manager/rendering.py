from pathlib import Path
from typing import Callable

from pydantic import dataclasses
from jinja2 import Environment
from manager.models import Image, Tag, Variant


@dataclasses.dataclass(frozen=True)
class RenderContext:
    image: Image
    tag: Tag
    all: list[Image]
    variant: Variant | None = None


def _resolve_base_image(ctx: RenderContext) -> Callable[[str], str]:
    def impl(name: str):
        found = [i for i in ctx.all if i.name == name and i.is_base_image]
        if len(found) == 1:
            return found[0].full_qualified_base_image_name
        else:
            raise RuntimeError(f"Could not resolve base image {name}")

    return impl


def _resolve_version(ctx: RenderContext) -> Callable[[str], str]:
    def impl(name: str):
        # In the new architecture, tags already have merged versions
        # So we just need to check the tag's versions
        version_from_tag = ctx.tag.versions.get(name, None)
        if version_from_tag is not None:
            return version_from_tag

        raise RuntimeError(f"Could not resolve version {name}")

    return impl


def render_test_config(context: RenderContext) -> str:
    env = Environment()
    env.filters["resolve_version"] = _resolve_version(context)

    tpl = env.from_string(context.image.test_config_path.read_text())
    full_qualified_image_name = f"{context.image.name}:{context.tag.name}"
    if context.variant is not None:
        full_qualified_image_name += f"-{context.variant.name}"

    return tpl.render(
        image=context.image,
        tag=context.tag,
        full_qualified_image_name=full_qualified_image_name,
    )


def render_dockerfile(context: RenderContext):
    env = Environment()
    env.filters["resolve_base_image"] = _resolve_base_image(context)
    env.filters["resolve_version"] = _resolve_version(context)

    variant_args = {}

    if context.variant is not None:
        # For variants, need to find the base tag name (without suffix)
        # The variant tag name is like "3.13.7-semantic", we need "3.13.7"
        base_tag_name = context.tag.name
        for base_tag in context.image.tags:
            if context.tag.name.startswith(base_tag.name):
                base_tag_name = base_tag.name
                break

        variant_args = {
            "base_image": f"{context.image.name}:{base_tag_name}",
        }
        tpl_file = context.variant.template_path
    else:
        tpl_file = context.image.dockerfile_template_path

    tpl = env.from_string(tpl_file.read_text())
    return tpl.render(image=context.image, tag=context.tag, **variant_args)
