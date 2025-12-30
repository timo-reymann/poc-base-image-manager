from pathlib import Path
from typing import Generator

from manager.model import ContainerImageDefinition


def discover_configurations(image_root: Path) -> Generator[ContainerImageDefinition, None, None]:
    for image_yaml in image_root.glob("**/image.yml"):
        yield ContainerImageDefinition.load_from_file(image_yaml)