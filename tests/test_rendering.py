from pathlib import Path
from manager.rendering import inject_rootfs_copy


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
