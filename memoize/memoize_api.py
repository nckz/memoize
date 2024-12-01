"""An abstract class with the framework necessary for function memoization.
Author: Nick Zwart
Date: 2024nov28
"""

# stdlib
import hashlib
import json
import threading


class DefaultLock:
    """A simple context manager to template mutex methods on."""

    def __init__(self):
        self.lock = threading.Lock()

    def __enter__(self):
        self.lock.acquire()
        return self.lock

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lock.release()


class MemoizeAPI:
    """An abstract class that serves as a common interface for various caching
    implementations.
    """

    def __init__(self, func, cache_prefix=""):
        """Initialize the calling function and a prefix that can be used to
        modify storage keys.
        """
        self.func = func
        self.func_name = self.func.__name__
        self.cache_prefix = cache_prefix

    def key(self, args_in, kwargs_in):
        """Return a key based on the hash and prefix."""
        base = f"{self.func_name}_{self.hash(args_in, kwargs_in)}"
        if self.cache_prefix == "":
            return base
        return f"{self.cache_prefix}_{base}"

    def get(self, key):
        """Return the corresponding cached item."""
        if self.check(key):
            with self.lock(key):
                return self.fetch(key)

    def put(self, key, data):
        """Run the function and store the data and return the function output."""
        if self.check(key):
            with self.lock(key):
                self.delete(key)
        self.store(key, data)
        return data

    def run(self, *args_in, **kwargs_in):
        """Execute the determine if the function should be run by checking
        cache, if so, run it and then push to cache.
        """
        okey = self.key(args_in, kwargs_in)

        if (out := self.get(okey)) is not None:
            print("cache hit", okey)
            return out

        data = self.func(*args_in, **kwargs_in)
        print("run", okey)
        return self.put(okey, data)

    def hash(self, args_in, kwargs_in):
        """Return a hash based on the input args. Default is JSON
        serialization.
        """
        return hashlib.sha512(
            json.dumps([args_in, kwargs_in]).encode("utf-8")
        ).hexdigest()

    def check(self, key):
        """Return True if the cache exists and false if it doesn't."""
        raise NotImplementedError

    def fetch(self, key):
        """Return the data based on the given key using the drivers specific to
        the desired storage method.
        """
        raise NotImplementedError

    def store(self, key, data):
        """Store that data based on the given key using the drivers specific to
        the desired storage method.
        """
        raise NotImplementedError

    def lock(self, key):
        """Lock the cache file or mutex the db command if necessary, block
        until lock is made.
        """
        return DefaultLock()

    def delete(self, key):
        """Remove the data corresponding to the given key using the drivers
        specific to the desired storage method.
        """
        pass
