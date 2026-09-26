"""One clock per Windows user, with a queued reveal request for repeat launches.

Mutex ownership is held for the entire application lifetime. Windows releases it
if the owner crashes. The event exists before ownership is attempted, so a reveal
request made during startup stays queued until the Tk loop is ready.
"""

import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path


def instance_name():
    # Stable across project copies, separate for each user's local profile.
    profile = os.path.normcase(os.path.abspath(os.environ.get("LOCALAPPDATA", Path.home())))
    identity = hashlib.sha256(profile.encode("utf-8")).hexdigest()[:32]
    return "Global\\DeathClock-" + identity


class SingleInstance:
    def __init__(self, name=None):
        self.name = name or instance_name()
        self._api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateMutexW": ([ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "CreateEventW": ([ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "WaitForSingleObject": ([wintypes.HANDLE, wintypes.DWORD], wintypes.DWORD),
            "SetEvent": ([wintypes.HANDLE], wintypes.BOOL),
            "ReleaseMutex": ([wintypes.HANDLE], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for function, (arguments, result) in signatures.items():
            getattr(self._api, function).argtypes = arguments
            getattr(self._api, function).restype = result
        self._mutex = self._event = None
        self.is_primary = False
        try:
            self._event = self._api.CreateEventW(None, False, False, self.name + "-show")
            if not self._event:
                raise ctypes.WinError(ctypes.get_last_error())
            self._mutex = self._api.CreateMutexW(None, False, self.name + "-owner")
            if not self._mutex:
                raise ctypes.WinError(ctypes.get_last_error())
            result = self._api.WaitForSingleObject(self._mutex, 0)
            if result in (0, 0x80):  # acquired, or previous owner crashed
                self.is_primary = True
            elif result != 0x102:  # timeout means another process owns it
                raise ctypes.WinError(ctypes.get_last_error())
        except BaseException:
            self.close()
            raise

    def request_show(self):
        if not self._api.SetEvent(self._event):
            raise ctypes.WinError(ctypes.get_last_error())

    def take_show_request(self):
        result = self._api.WaitForSingleObject(self._event, 0)
        if result == 0x102:
            return False
        if result != 0:
            raise ctypes.WinError(ctypes.get_last_error())
        return True  # auto-reset event consumes the request once

    def close(self):
        if self._mutex:
            if self.is_primary:
                self._api.ReleaseMutex(self._mutex)
            self._api.CloseHandle(self._mutex)
        if self._event:
            self._api.CloseHandle(self._event)
        self._mutex = self._event = None
        self.is_primary = False

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
