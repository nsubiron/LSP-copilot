import os
import textwrap

import sublime


def get_project_relative_path(file_path: str) -> str:
    ret = file_path
    for folder in sublime.active_window().folders():
        try:
            ret = min(ret, os.path.relpath(file_path, folder), key=len)
        except ValueError:
            pass
    return ret


def reformat(text: str) -> str:
    """Remove common indentaions and then trim."""
    return textwrap.dedent(text).strip()
