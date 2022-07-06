from .constants import (
    NTFY_LOG_MESSAGE,
    NTFY_STATUS_NOTIFICATION,
    PACKAGE_NAME,
    PACKAGE_VERSION,
    REQ_CHECK_STATUS,
    REQ_GET_COMPLETIONS,
    REQ_SET_EDITOR_INFO,
)
from .types import (
    CopilotPayloadCompletions,
    CopilotPayloadLogMessage,
    CopilotPayloadSignInConfirm,
    CopilotPayloadStatusNotification,
)
from .utils import clear_completion_preview
from .utils import get_project_relative_path
from .utils import set_view_is_waiting_completion
from LSP.plugin import filename_to_uri
from LSP.plugin import Request
from LSP.plugin import Session
from LSP.plugin.core.typing import Optional, Tuple
from lsp_utils import ApiWrapperInterface
from lsp_utils import notification_handler
from lsp_utils import NpmClientHandler
import functools
import os
import sublime
import weakref


def plugin_loaded():
    CopilotPlugin.setup()


def plugin_unloaded():
    CopilotPlugin.cleanup()
    CopilotPlugin.plugin_mapping.clear()


class CopilotPlugin(NpmClientHandler):
    package_name = PACKAGE_NAME
    server_directory = "language-server"
    server_binary_path = os.path.join(server_directory, "copilot", "dist", "agent.js")

    plugin_mapping = weakref.WeakValueDictionary()  # type: weakref.WeakValueDictionary[int, CopilotPlugin]
    _has_signed_in = False

    def __init__(self, session: "weakref.ref[Session]") -> None:
        super().__init__(session)
        sess = session()
        if sess:
            self.plugin_mapping[sess.window.id()] = self

    def on_ready(self, api: ApiWrapperInterface) -> None:
        def on_check_status(result: CopilotPayloadSignInConfirm, failed: bool) -> None:
            self.set_has_signed_in(result.get("status") == "OK")

        def on_set_editor_info(result: str, failed: bool) -> None:
            pass

        api.send_request(REQ_CHECK_STATUS, {}, on_check_status)
        api.send_request(
            REQ_SET_EDITOR_INFO,
            {
                "editorInfo": {
                    "name": "Sublime Text",
                    "version": sublime.version(),
                },
                "editorPluginInfo": {
                    "name": PACKAGE_NAME,
                    "version": PACKAGE_VERSION,
                },
            },
            on_set_editor_info,
        )

    @classmethod
    def minimum_node_version(cls) -> Tuple[int, int, int]:
        # this should be aligned with VSCode's Nodejs version
        return (16, 0, 0)

    @classmethod
    def get_has_signed_in(cls) -> bool:
        return cls._has_signed_in

    @classmethod
    def set_has_signed_in(cls, value: bool) -> None:
        cls._has_signed_in = value
        if value:
            sublime.status_message("✈ Copilot has been signed in.")
        else:
            sublime.status_message("⚠ Copilot has NOT been signed in.")

    @classmethod
    def plugin_from_view(cls, view: sublime.View) -> Optional["CopilotPlugin"]:
        window = view.window()
        if not window:
            return None
        self = cls.plugin_mapping.get(window.id())
        if not (self and self.is_valid_for_view(view)):
            return None
        return self

    def is_valid_for_view(self, view: sublime.View) -> bool:
        session = self.weaksession()
        return bool(session and session.session_view_for_view_async(view))

    @notification_handler(NTFY_LOG_MESSAGE)
    def _handle_log_message_notification(self, payload: CopilotPayloadLogMessage) -> None:
        pass

    @notification_handler(NTFY_STATUS_NOTIFICATION)
    def _handle_status_notification(self, payload: CopilotPayloadStatusNotification) -> None:
        pass

    def request_get_completions(self, view: sublime.View) -> None:
        clear_completion_preview(view)

        session = self.weaksession()
        syntax = view.syntax()
        sel = view.sel()
        if not (self.get_has_signed_in() and session and syntax and len(sel) == 1):
            return

        cursor = sel[0]
        file_path = view.file_name() or ""
        row, col = view.rowcol(cursor.begin())
        params = {
            "doc": {
                "source": view.substr(sublime.Region(0, view.size())),
                "tabSize": view.settings().get("tab_size", 4),
                "indentSize": 1,  # there is no such concept in ST
                "insertSpaces": False,  # always use TAB and let ST auto converts it accordingly
                "path": file_path,
                "uri": file_path and filename_to_uri(file_path),
                "relativePath": get_project_relative_path(file_path),
                "languageId": syntax.scope.rpartition(".")[2],  # @todo there is a mapping in LSP already?
                "position": {"line": row, "character": col},
            }
        }

        set_view_is_waiting_completion(view, True)
        session.send_request_async(
            Request(REQ_GET_COMPLETIONS, params),
            functools.partial(self._on_get_completions_async, view, region=cursor.to_tuple()),
        )

    def _on_get_completions_async(
        self,
        view: sublime.View,
        payload: CopilotPayloadCompletions,
        region: Tuple[int, int],
    ) -> None:
        set_view_is_waiting_completion(view, False)

        # re-request completions because the cursor position changed during awaiting Copilot's response
        if view.sel()[0].to_tuple() != region:
            self.request_get_completions(view)
            return

        completions = payload.get("completions")
        if not completions:
            return

        sublime.set_timeout_async(
            lambda: view.run_command(
                "copilot_preview_completions",
                {"completions": completions, "region": region},
            )
        )
