import logging
from typing import Dict, List, Optional, Tuple

import libcst as cst

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


TrackedObjectState = Literal['pending', 'processed', 'failed']


class BaseProgressTracker:
    """Base class for tracking progress during documentation generation"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('docugen')
        self.tracked_object: Dict[str, List[cst.CSTNode]] = {}

    def track_file(self, file_path: str) -> None:
        """Track when a file is being processed"""
        if file_path not in self.tracked_object:
            self.tracked_object[file_path] = []

    def track_object(
        self, file_path: str, node: cst.CSTNode, state: TrackedObjectState
    ) -> None:
        """Track when an object (class/function) is being processed"""
        if file_path not in self.tracked_object:
            self.track_file(file_path)
        self.tracked_object[file_path].append((node, state))


class ProgressTracker(BaseProgressTracker):
    """Concrete implementation of progress tracker with tree-like display and state management"""

    def track_file(self, file_path: str) -> None:
        """Display file being processed and store it"""
        super().track_file(file_path)
        print(f'\n{file_path}')
        self.logger.info(f'Processing {file_path}')

    def track_object(
        self, file_path: str, node: cst.CSTNode, state: TrackedObjectState
    ) -> None:
        """Display a tree-like structure of processed objects in real-time and store the node"""
        super().track_object(file_path, node, state)
        obj_type = 'class' if isinstance(node, cst.ClassDef) else 'function'
        obj_name = node.name.value
        print(f'  | {obj_type} {obj_name} [{state.upper()}]')

    def get_tracked_objects(
        self, file_path: str
    ) -> List[Tuple[cst.CSTNode, TrackedObjectState]]:
        """Get all tracked objects for a specific file"""
        return self.tracked_object.get(file_path, [])

    def get_all_tracked_files(self) -> List[str]:
        """Get all tracked files"""
        return list(self.tracked_object.keys())
