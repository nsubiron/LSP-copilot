import os
import textwrap
import traceback

import mdpopups
import sublime
from LSP.plugin.core.sessions import Session
from LSP.plugin.core.types import basescope2languageid
from LSP.plugin.core.typing import Any, Callable, Dict, Generator, Iterable, List, Optional, TypeVar, Union
from LSP.plugin.core.url import filename_to_uri

from .constants import COPILOT_VIEW_SETTINGS_PREFIX, PACKAGE_NAME
from .types import CopilotPayloadCompletion, CopilotPayloadPanelSolution

T = TypeVar("T")
T_Number = TypeVar("T_Number", bound=Union[int, float])


def all_views(
    window: Optional[sublime.Window] = None,
    *,
    include_transient: bool = False
    # format delimiter
) -> Generator[sublime.View, None, None]:
    windows = [window] if window else sublime.windows()
    for window in windows:
        yield from window.views(include_transient=include_transient)


def all_sheets(
    window: Optional[sublime.Window] = None,
    *,
    include_transient: bool = False
    # format delimiter
) -> Generator[sublime.Sheet, None, None]:
    windows = [window] if window else sublime.windows()
    for window in windows:
        if include_transient:
            yield from filter(None, map(window.transient_sheet_in_group, range(window.num_groups())))
        yield from window.sheets()


def clamp(val: T_Number, min_val: Optional[T_Number] = None, max_val: Optional[T_Number] = None) -> T_Number:
    """Returns the bounded value of `val` in the range of `[min_val, max_val]`."""
    if min_val is not None and val < min_val:  # type: ignore
        return min_val
    if max_val is not None and val > max_val:  # type: ignore
        return max_val
    return val


def find_sheet_by_id(id: int) -> Optional[sublime.Sheet]:
    return first(all_sheets(include_transient=True), lambda sheet: sheet.id() == id)


def find_view_by_id(id: int) -> Optional[sublime.View]:
    return first(all_views(include_transient=True), lambda view: view.id() == id)


def first(items: Iterable[T], test: Optional[Callable[[T], bool]] = None, default: Optional[T] = None) -> Optional[T]:
    """
    Gets the first item which satisfies the `test`. Otherwise, `default`.
    If `test` is not given or `None`, the first truthy item will be returned.
    """
    return next(filter(test, items), default)


def get_copilot_view_setting(view: sublime.View, key: str, default: Any = None) -> Any:
    return view.settings().get("{}.{}".format(COPILOT_VIEW_SETTINGS_PREFIX, key), default)


def set_copilot_view_setting(view: sublime.View, key: str, value: Any) -> None:
    view.settings().set("{}.{}".format(COPILOT_VIEW_SETTINGS_PREFIX, key), value)


def erase_copilot_view_setting(view: sublime.View, key: str) -> None:
    view.settings().erase("{}.{}".format(COPILOT_VIEW_SETTINGS_PREFIX, key))


def get_project_relative_path(path: str) -> str:
    relpath = path
    for folder in sublime.active_window().folders():
        try:
            relpath = min(relpath, os.path.relpath(path, folder), key=len)
        except ValueError:
            pass
    return relpath


def get_setting(session: Session, key: str, default: Optional[Union[str, bool, List[str]]] = None) -> Any:
    value = session.config.settings.get(key)
    if value is None:
        return default
    return value


def get_view_language_id(view: sublime.View) -> str:
    syntax = view.syntax() or sublime.find_syntax_by_name("Plain Text")[0]
    return basescope2languageid(syntax.scope)


def message_dialog(msg_: str, *args, error_: bool = False, console_: bool = False, **kwargs) -> None:
    full_msg = "[{}] {}".format(PACKAGE_NAME, msg_.format(*args, **kwargs))
    messenger = sublime.error_message if error_ else sublime.message_dialog
    messenger(full_msg)

    if console_:
        print(full_msg)


def ok_cancel_dialog(msg_: str, *args, **kwargs) -> bool:
    return sublime.ok_cancel_dialog("[{}] {}".format(PACKAGE_NAME, msg_.format(*args, **kwargs)))


def prepare_completion_request(view: sublime.View) -> Optional[Dict[str, Any]]:
    sel = view.sel()
    if len(sel) != 1:
        return None

    file_path = view.file_name() or ""
    row, col = view.rowcol(sel[0].begin())
    return {
        "doc": {
            "source": view.substr(sublime.Region(0, view.size())),
            "tabSize": view.settings().get("tab_size", 4),
            "indentSize": 1,  # there is no such concept in ST
            "insertSpaces": view.settings().get("translate_tabs_to_spaces", False),
            "path": file_path,
            "uri": file_path and filename_to_uri(file_path),
            "relativePath": get_project_relative_path(file_path),
            "languageId": get_view_language_id(view),
            "position": {"line": row, "character": col},
        }
    }


def preprocess_completions(view: sublime.View, completions: List[CopilotPayloadCompletion]) -> None:
    for completion in completions:
        completion["point"] = view.text_point(
            completion["position"]["line"],
            completion["position"]["character"],
        )
        _generate_completion_region(view, completion)


def preprocess_panel_completions(view: sublime.View, completions: List[CopilotPayloadPanelSolution]) -> None:
    for completion in completions:
        _generate_completion_region(view, completion)


def reformat(text: str) -> str:
    """Remove common indentations and then trim."""
    return textwrap.dedent(text).strip()


def remove_prefix(s: str, prefix: str) -> str:
    """Remove the prefix from the string. I.e., str.removeprefix in Python 3.9."""
    return s[len(prefix) :] if s.startswith(prefix) else s


def remove_suffix(s: str, suffix: str) -> str:
    """Remove the suffix from the string. I.e., str.removesuffix in Python 3.9."""
    # suffix="" should not call s[:-0]
    return s[: -len(suffix)] if suffix and s.endswith(suffix) else s


def status_message(msg_: str, *args, icon_: Optional[str] = "✈", console_: bool = False, **kwargs) -> None:
    prefix = "{} ".format(icon_) if icon_ else ""
    full_msg = "{}Copilot {}".format(prefix, msg_.format(*args, **kwargs))
    sublime.status_message(full_msg)

    if console_:
        print(full_msg)


def unique(items: Iterable[T], *, key: Optional[Callable[[T], Any]] = None) -> Generator[T, None, None]:
    key = key or (lambda x: x)
    seen = set()
    for item in items:
        k = key(item)
        if k not in seen:
            yield item
            seen.add(k)


def _generate_completion_region(
    view: sublime.View,
    completion: Union[CopilotPayloadCompletion, CopilotPayloadPanelSolution],
) -> None:
    completion["region"] = (
        view.text_point(
            completion["range"]["start"]["line"],
            completion["range"]["start"]["character"],
        ),
        view.text_point(
            completion["range"]["end"]["line"],
            completion["range"]["end"]["character"],
        ),
    )


def mdpopups_update_transient_html_sheet(
    window: sublime.Window,
    sheet: sublime.HtmlSheet,
    contents: str,
    md: bool = True,
    css: Optional[str] = None,
    wrapper_class: Optional[str] = None,
    template_vars: Optional[Any] = None,
    template_env_options: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """Update a transient HTML sheet."""
    # for a transient sheet, `.window()` returns `None` so we can't just use `mdpopups.update_html_sheet`
    view = window.create_output_panel("mdpopups-dummy", unlisted=True)

    try:
        html = mdpopups._create_html(
            view,
            contents,
            md,
            css,
            css_type=mdpopups.SHEET,
            wrapper_class=wrapper_class,
            template_vars=template_vars,
            template_env_options=template_env_options,
            **kwargs
        )  # type: str
    except Exception:
        mdpopups._log(traceback.format_exc())
        html = mdpopups.IDK

    sheet.set_contents(html)
