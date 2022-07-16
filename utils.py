import os
import textwrap

import sublime

from LSP.plugin.core.sessions import Session
from LSP.plugin.core.typing import Optional, Union, List, Any


def get_project_relative_path(file_path: str) -> str:
    ret = file_path
    for folder in sublime.active_window().folders():
        try:
            ret = min(ret, os.path.relpath(file_path, folder), key=len)
        except ValueError:
            pass
    return ret


def get_setting(session: Session, key: str, default: Optional[Union[str, bool, List[str]]] = None) -> Any:
    value = session.config.settings.get(key)
    if value is None:
        return default
    return value


def reformat(text: str) -> str:
    """Remove common indentations and then trim."""
    return textwrap.dedent(text).strip()
