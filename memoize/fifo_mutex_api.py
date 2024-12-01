"""An abstract class with the framework necessary for function memoization.
Author: Nick Zwart
Date: 2024nov28
"""

# stdlib
from datetime import datetime
import os
import socket
import time


class FifoMutex_API:
    """An example of a file based mutex with no direct IPC."""

    def __init__(
        self, key, lock_prefix, lock_path="/tmp", deadlock_age_s=3600, poll_time_s=30
    ):
        """Set all patterns that make the target and proposing instance unique."""
        self.lock_prefix = lock_prefix
        self.lock_path = lock_path
        self.key = key
        self.full_prefix = f"{self.lock_prefix}_{self.key}"
        self.deadlock_age_s = deadlock_age_s
        self.poll_time_s = poll_time_s
        self._lock = False

    def uuid(self):
        """Return a unique global instance."""
        return f"{socket.gethostname()}_{id(self)}"

    def lock_key(self):
        """Return the lock name."""
        base = f"{self.uuid()}"
        return f"{self.full_prefix}_{base}"

    def full_key_path(self, lock=None):
        if lock is not None:
            return os.path.join(self.lock_path, lock)
        return os.path.join(self.lock_path, self.lock_key())

    def yield_matching_prefix(self):
        """Return a list of lock names belonging to the same prefix."""
        for item in os.listdir(self.lock_path):
            if item.startswith(self.full_prefix):
                yield item

    def get_matching_key(self):
        """Return a list of lock names belonging to this instance."""
        for item in self.yield_matching_prefix():
            if item.startswith(self.lock_key()):
                return item
        return None

    def get_lock_time(self, lock=None):
        """Return the lock time for this instance."""
        if lock is not None:
            fpath = self.full_key_path(lock)
            fdate = datetime.fromtimestamp(os.path.getctime(fpath))
            return fdate

        item = self.get_matching_key()
        fpath = self.full_key_path(item)
        fdate = datetime.fromtimestamp(os.path.getctime(fpath))
        return fdate

    def get_oldest_lock(self):
        """Return the oldest one."""
        return self.get_locks()[0]

    def get_locks(self):
        """Return the oldest one."""
        locks = []
        for item in self.yield_matching_prefix():
            fpath = os.path.join(self.lock_path, item)
            locks.append((self.get_lock_time(item), fpath))
        return sorted(locks)

    def check(self):
        """Return true if the lock for this instance exists."""
        return self.get_matching_key() is not None

    def cast_lock(self):
        """Send a lock file with the current timestamp."""
        with open(self.lock_key(), "w") as fil:
            fil.write("")

    def delete(self, lock):
        """Remove the lock file."""
        os.remove(lock)

    def wait_for_lock(self):
        """Wait until this instance holds the oldest timestamp."""

        self.cast_lock()
        while self.full_key_path() != (cur := self.get_oldest_lock())[1]:
            print(self.lock_key(), "waiting for lock... cur:", cur)
            time.sleep(self.poll_time_s)

            # if the lock file is gone, make a new one
            if not self.check():
                print("recast lock")
                self.cast_lock()

            # check for deadlocks
            if (datetime.now() - cur[0]).seconds > self.deadlock_age_s:
                print("deleting old lock", cur)
                self.delete(cur[1])

        self._lock = True

    def lock(self):
        """Acquire a lock, block until it has been gotten."""
        self.wait_for_lock()
        return self

    def unlock(self):
        """Remove the lock."""
        self._lock = False
        try:
            self.delete(self.full_key_path())
        except FileNotFoundError:
            print(f"'{self.full_key_path()}' not found on close.")

    def __enter__(self):
        return self.lock()

    def __exit__(self, *_):
        return self.unlock()
