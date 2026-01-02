from pathlib import Path
from manager.models import Image, Tag, Variant
from manager.rendering import inject_rootfs_copy, RenderContext, render_dockerfile


def test_render_dockerfile_injects_copy_when_rootfs_exists(tmp_path):
    """Test render_dockerfile injects COPY when has_rootfs is True"""
    tpl = tmp_path / "Dockerfile.tmpl"
    tpl.write_text("FROM base:1.0\nRUN echo hello")

    image = Image(
        name="test",
        path=tmp_path,
        template_path=tpl,
        versions={},
        variables={},
        tags=[],
        variants=[],
        is_base_image=False,
        extends=None,
        aliases={},
        rootfs_user="1000:1000",
        rootfs_copy=True
    )
    tag = Tag(name="1.0", versions={}, variables={}, rootfs_user="1000:1000", rootfs_copy=True)

    ctx = RenderContext(image=image, tag=tag, all=[], has_rootfs=True)
    result = render_dockerfile(ctx)

    assert "COPY --chown=1000:1000 rootfs/ /" in result


def test_render_dockerfile_no_inject_when_rootfs_copy_false(tmp_path):
    """Test render_dockerfile skips injection when rootfs_copy is False"""
    tpl = tmp_path / "Dockerfile.tmpl"
    tpl.write_text("FROM base:1.0\nRUN echo hello")

    image = Image(
        name="test",
        path=tmp_path,
        template_path=tpl,
        versions={},
        variables={},
        tags=[],
        variants=[],
        is_base_image=False,
        extends=None,
        aliases={},
        rootfs_user="0:0",
        rootfs_copy=False
    )
    tag = Tag(name="1.0", versions={}, variables={}, rootfs_user="0:0", rootfs_copy=False)

    ctx = RenderContext(image=image, tag=tag, all=[], has_rootfs=True)
    result = render_dockerfile(ctx)

    assert "COPY" not in result


def test_render_dockerfile_no_inject_when_no_rootfs(tmp_path):
    """Test render_dockerfile skips injection when has_rootfs is False"""
    tpl = tmp_path / "Dockerfile.tmpl"
    tpl.write_text("FROM base:1.0\nRUN echo hello")

    image = Image(
        name="test",
        path=tmp_path,
        template_path=tpl,
        versions={},
        variables={},
        tags=[],
        variants=[],
        is_base_image=False,
        extends=None,
        aliases={},
    )
    tag = Tag(name="1.0", versions={}, variables={})

    ctx = RenderContext(image=image, tag=tag, all=[], has_rootfs=False)
    result = render_dockerfile(ctx)

    assert "COPY" not in result


def test_render_dockerfile_variant_uses_variant_rootfs_user(tmp_path):
    """Test render_dockerfile uses variant.rootfs_user for variants"""
    base_tpl = tmp_path / "Dockerfile.tmpl"
    base_tpl.write_text("FROM base:1.0\nRUN echo base")

    variant_tpl = tmp_path / "Dockerfile.variant.tmpl"
    variant_tpl.write_text("FROM {{ base_image }}\nRUN echo variant")

    image = Image(
        name="test",
        path=tmp_path,
        template_path=base_tpl,
        versions={},
        variables={},
        tags=[Tag(name="1.0", versions={}, variables={})],
        variants=[],
        is_base_image=False,
        extends=None,
        aliases={},
        rootfs_user="0:0",
        rootfs_copy=True
    )
    variant = Variant(
        name="myvariant",
        template_path=variant_tpl,
        tags=[],
        aliases={},
        rootfs_user="2000:2000",
        rootfs_copy=True
    )
    tag = Tag(name="1.0-myvariant", versions={}, variables={}, rootfs_user="1000:1000", rootfs_copy=True)

    ctx = RenderContext(image=image, tag=tag, all=[], variant=variant, has_rootfs=True)
    result = render_dockerfile(ctx)

    # Should use variant's rootfs_user, not tag's
    assert "COPY --chown=2000:2000 rootfs/ /" in result


def test_inject_rootfs_copy_after_first_from():
    """Test COPY is injected after first FROM"""
    dockerfile = """FROM base:1.0
RUN apt-get update
"""
    result = inject_rootfs_copy(dockerfile, "0:0")
    expected = """FROM base:1.0
COPY --chown=0:0 rootfs/ /
RUN apt-get update
"""
    assert result == expected


def test_inject_rootfs_copy_with_custom_user():
    """Test COPY uses custom user"""
    dockerfile = "FROM base:1.0\nRUN echo hello"
    result = inject_rootfs_copy(dockerfile, "1000:1000")
    assert "COPY --chown=1000:1000 rootfs/ /" in result


def test_inject_rootfs_copy_multi_stage():
    """Test COPY is injected only after FIRST FROM in multi-stage"""
    dockerfile = """FROM builder:1.0 AS build
RUN make
FROM runtime:1.0
COPY --from=build /app /app
"""
    result = inject_rootfs_copy(dockerfile, "0:0")
    lines = result.split("\n")
    # COPY should be after first FROM, not after second
    assert lines[1] == "COPY --chown=0:0 rootfs/ /"
    assert "COPY --chown=0:0 rootfs/ /" not in "\n".join(lines[3:])


def test_inject_skips_if_already_present():
    """Test injection is skipped if COPY rootfs/ already exists"""
    dockerfile = """FROM base:1.0
COPY rootfs/ /
RUN echo hello
"""
    result = inject_rootfs_copy(dockerfile, "0:0")
    assert result == dockerfile  # Unchanged
    assert result.count("COPY") == 1


def test_inject_skips_if_copy_rootfs_with_chown():
    """Test injection is skipped if COPY --chown=X rootfs/ already exists"""
    dockerfile = """FROM base:1.0
COPY --chown=1000:1000 rootfs/ /custom/path
"""
    result = inject_rootfs_copy(dockerfile, "0:0")
    assert result == dockerfile


def test_inject_preserves_from_args():
    """Test injection works with FROM args"""
    dockerfile = """ARG BASE_IMAGE=base:1.0
FROM ${BASE_IMAGE}
RUN echo hello
"""
    result = inject_rootfs_copy(dockerfile, "0:0")
    lines = result.split("\n")
    assert lines[0] == "ARG BASE_IMAGE=base:1.0"
    assert lines[1] == "FROM ${BASE_IMAGE}"
    assert lines[2] == "COPY --chown=0:0 rootfs/ /"
