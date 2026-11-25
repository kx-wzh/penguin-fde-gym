"""Filesystem boundaries between the Harbor agent, the simulator and the verifier."""

import contextlib
import os
from pathlib import Path
import pwd
import signal
import stat
import time


VERIFIER_LOGS = Path("/logs/verifier")
WORKSPACE = Path("/app")
REWARD_FILES = ("reward.json", "reward.txt")


def protect_verifier_logs():
    # Harbor bind-mounts this directory and reads it as the host user during
    # verification. Keep its existing owner and remove access for other users.
    logs = VERIFIER_LOGS.lstat()
    parent = VERIFIER_LOGS.parent.lstat()
    if not stat.S_ISDIR(logs.st_mode) or not stat.S_ISDIR(parent.st_mode) or parent.st_uid != 0 or parent.st_mode & 0o022:
        raise RuntimeError("Verifier log mount has an unsafe parent or type")
    workspace_users = {pwd.getpwnam(name).pw_uid for name in ("fde-agent", "fde-delivery")}
    if logs.st_uid in workspace_users:
        raise RuntimeError("Host verifier log owner overlaps a task user")
    VERIFIER_LOGS.chmod(0o700)
    for filename in REWARD_FILES:
        (VERIFIER_LOGS / filename).unlink(missing_ok=True)


def stop_agent_processes():
    """Stop background processes before validating the workspace for root replay."""
    agent_uid = str(pwd.getpwnam("fde-agent").pw_uid)
    deadline = time.monotonic() + 5
    while True:
        found = False
        for proc in Path("/proc").iterdir():
            if not proc.name.isdecimal():
                continue
            try:
                pidfd = os.pidfd_open(int(proc.name))
            except ProcessLookupError:
                continue
            try:
                fields = dict(line.split(":", 1) for line in (proc / "status").read_text().splitlines())
                if fields["State"].split()[0] != "Z" and agent_uid in fields["Uid"].split():
                    found = True
                    signal.pidfd_send_signal(pidfd, signal.SIGKILL)
            except (FileNotFoundError, ProcessLookupError):
                continue
            finally:
                os.close(pidfd)
        if not found:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError("Could not stop all FDE-Gym agent processes")
        time.sleep(0.05)


def raise_walk_error(error):
    raise error


def verify_workspace_tree(workspace):
    """Accept ordinary directories and regular files in the replay input."""
    for directory, dirs, files in os.walk(workspace, onerror=raise_walk_error):
        for name in dirs + files:
            entry = Path(directory, name)
            info = entry.lstat()
            if not (stat.S_ISDIR(info.st_mode) or (stat.S_ISREG(info.st_mode) and info.st_nlink == 1)):
                raise RuntimeError("FDE-Gym replay accepts only directories and regular files without hard links")


@contextlib.contextmanager
def workspace_dir(root, *parts, create=False):
    """Open a pilot directory relative to trusted descriptors, without following links."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(root, flags)
    try:
        for part in parts:
            if create:
                try:
                    os.mkdir(part, dir_fd=fd)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


@contextlib.contextmanager
def open_pilot_request(workspace):
    with workspace_dir(workspace, "system", "fleet") as fd:
        # O_NONBLOCK keeps a special file from stalling the simulator before fstat.
        file_fd = os.open("trial_request.json", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(file_fd, "rb") as file:
            info = os.fstat(file.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OSError("Expected a regular trial request file")
            yield file


@contextlib.contextmanager
def open_pilot_csv(workspace, day):
    with workspace_dir(workspace, "data", "trials", create=True) as fd:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        file_fd = os.open(f"trial_{day}.csv", flags, 0o644, dir_fd=fd)
        with os.fdopen(file_fd, "w", encoding="utf-8", newline="") as file:
            yield file


if __name__ == "__main__":
    protect_verifier_logs()
