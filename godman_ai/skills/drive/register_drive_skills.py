"""Register mock drive skills with a registry."""

from godman_ai.skills.drive.skills import (
    drive_copy,
    drive_download,
    drive_move,
    drive_search,
    drive_share,
    drive_upload,
)


try:
    from godman_ai.skill_registry import SkillRegistry  # type: ignore
except ImportError:

    class SkillRegistry:
        def __init__(self) -> None:
            self.skills = {}

        def register(self, name: str, func) -> None:
            self.skills[name] = func


def register(registry: "SkillRegistry") -> None:
    registry.register("drive.upload", drive_upload)
    registry.register("drive.download", drive_download)
    registry.register("drive.search", drive_search)
    registry.register("drive.move", drive_move)
    registry.register("drive.copy", drive_copy)
    registry.register("drive.share", drive_share)
