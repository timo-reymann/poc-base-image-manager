from typing import TYPE_CHECKING

from manager.config import VariantConfig
from manager.merger import Merger

if TYPE_CHECKING:
    from manager.models import Tag


class TagGenerator:
    """Generates variant tags from base tags"""

    @staticmethod
    def generate_variant_tags(
        base_tags: list["Tag"],
        variant: VariantConfig,
        image_versions: dict[str, str],
        image_variables: dict[str, str],
    ) -> list["Tag"]:
        """
        Generate variant tags from base tags.
        Each variant tag:
        - Has base tag name + variant suffix
        - Has merged versions: image → base_tag → variant
        - Has merged variables: image → base_tag → variant
        """
        # Import at runtime to avoid circular import
        from manager.models import Tag

        variant_tags = []

        for base_tag in base_tags:
            # Create suffixed name
            variant_tag_name = base_tag.name + variant.tag_suffix

            # Merge versions: image → base_tag → variant
            merged_versions = Merger.merge(
                image_versions, base_tag.versions, variant.versions
            )

            # Merge variables: image → base_tag → variant
            merged_variables = Merger.merge(
                image_variables, base_tag.variables, variant.variables
            )

            variant_tags.append(
                Tag(
                    name=variant_tag_name,
                    versions=merged_versions,
                    variables=merged_variables,
                )
            )

        return variant_tags
