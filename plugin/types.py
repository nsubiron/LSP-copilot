from collections import namedtuple

from LSP.plugin.core.typing import Any, Callable, List, Literal, Tuple, TypedDict, TypeVar

T_Callable = TypeVar("T_Callable", bound=Callable[..., Any])

AccountStatus = namedtuple("AccountStatus", ["has_signed_in", "is_authorized"])

# ---------------------------- #
# realted to Sublime Text APIs #
# ---------------------------- #

StPoint = int
StRegion = Tuple[StPoint, StPoint]

StLayout = TypedDict(
    "StLayout",
    {
        "cols": List[float],
        "rows": List[float],
        "cells": List[List[int]],
    },
    total=True,
)

NetworkProxy = TypedDict(
    "NetworkProxy",
    {
        "host": str,
        "port": int,
        "username": str,
        "password": str,
        "rejectUnauthorized": bool,
    },
    total=True,
)

# --------------- #
# Copilot payload #
# --------------- #

CopilotPayloadCompletionPosition = TypedDict(
    "CopilotPayloadCompletionPosition",
    {
        "character": int,
        "line": int,
    },
    total=True,
)

CopilotPayloadCompletionRange = TypedDict(
    "CopilotPayloadCompletionRange",
    {
        "start": CopilotPayloadCompletionPosition,
        "end": CopilotPayloadCompletionPosition,
    },
    total=True,
)

CopilotPayloadCompletion = TypedDict(
    "CopilotPayloadCompletion",
    {
        "text": str,
        "position": CopilotPayloadCompletionPosition,
        "uuid": str,
        "range": CopilotPayloadCompletionRange,
        "displayText": str,
        # injected for convenience
        "point": StPoint,
        "region": StRegion,
    },
    total=True,
)

CopilotPayloadCompletions = TypedDict(
    "CopilotPayloadCompletions",
    {
        "completions": List[CopilotPayloadCompletion],
    },
    total=True,
)

CopilotPayloadGetVersion = TypedDict(
    "CopilotPayloadGetVersion",
    {
        "version": str,
    },
    total=True,
)

CopilotPayloadNotifyAccepted = TypedDict(
    "CopilotPayloadNotifyAccepted",
    {
        "uuid": str,
    },
    total=True,
)


CopilotPayloadNotifyRejected = TypedDict(
    "CopilotPayloadNotifyRejected",
    {
        "uuids": List[str],
    },
    total=True,
)

CopilotPayloadSignInInitiate = TypedDict(
    "CopilotPayloadSignInInitiate",
    {
        "verificationUri": str,
        "status": str,
        "userCode": str,
        "expiresIn": int,
        "interval": int,
    },
    total=True,
)

CopilotPayloadSignInConfirm = TypedDict(
    "CopilotPayloadSignInConfirm",
    {
        "status": Literal["AlreadySignedIn", "MaybeOk", "NotAuthorized", "NotSignedIn", "OK"],
        "user": str,
    },
    total=True,
)

CopilotPayloadSignOut = TypedDict(
    "CopilotPayloadSignOut",
    {
        "status": Literal["NotSignedIn"],
    },
    total=True,
)

CopilotPayloadLogMessage = TypedDict(
    "CopilotPayloadLogMessage",
    {
        "metadataStr": str,
        "extra": str,
        "level": int,
        "message": str,
    },
    total=True,
)

CopilotPayloadStatusNotification = TypedDict(
    "CopilotPayloadStatusNotification",
    {
        "message": str,
        "status": Literal["InProgress", "Normal"],
    },
    total=True,
)

CopilotPayloadPanelSolution = TypedDict(
    "CopilotPayloadPanelSolution",
    {
        "displayText": str,
        "solutionId": str,
        "score": int,
        "panelId": str,
        "completionText": str,
        "range": CopilotPayloadCompletionRange,
        # injected for convenience
        "region": StRegion,
    },
    total=True,
)

CopilotPayloadPanelCompletionSolutionCount = TypedDict(
    "CopilotPayloadPanelCompletionSolutionCount",
    {
        "solutionCountTarget": int,
    },
    total=True,
)
