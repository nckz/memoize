"""An abstract class with the framework necessary for function memoization.
Author: Nick Zwart
Date: 2024nov28
"""

# stdlib
import hashlib
import inspect
import pickle
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

    See https://code.activestate.com/recipes/52201/ for a recipe in making this
    class an encapsulating class.
    """

    def __init__(
        self,
        func,
        cache_prefix="",
        ignore_args=None,
        ignore_kwargs=None,
        delim="_",
        invalidate=False,
        verbose=False,
    ):
        """Initialize the calling function and a prefix that can be used to
        modify storage keys.
        """
        self.func = func
        self.func_name = self.func.__name__
        self.cache_prefix = cache_prefix
        self.ignore_args = ignore_args
        self.ignore_kwargs = ignore_kwargs
        self.delim = delim
        self.verbose = verbose
        self.invalidate = invalidate

        # get default kwargs
        sig = inspect.signature(self.func)
        self.default_kwargs = {}
        for parm in sig.parameters.values():
            if parm.default is not inspect.Parameter.empty:
                self.default_kwargs[parm.name] = parm.default

    def __call__(self, *args, **kwargs):
        """Execute the 'run' function as though this object were are function
        object.
        """
        return self.run(*args, **kwargs)

    def key(self, args_in, kwargs_in):
        """Return a key based on the hash and prefix."""
        base = f"{self.func_name}{self.delim}{self.hash(args_in, kwargs_in)}"
        if self.cache_prefix == "":
            return base
        return f"{self.cache_prefix}{self.delim}{base}"

    def get(self, key):
        """Return the corresponding cached item."""
        if self.check(key):
            with self.lock(key):
                return self.fetch(key)

    def put(self, key, data):
        """Run the function and store the data and return the function output."""
        if self.check(key):
            raise KeyError(f"{key} already exists!, 'put' failed.")
        else:
            with self.lock(key):
                self.store(key, data)
        return data

    def run(self, *args_in, **kwargs_in):
        """Execute the determine if the function should be run by checking
        cache, if so, run it and then push to cache.
        """
        okey = self.key(args_in, kwargs_in)

        if self.invalidate:
            if self.verbose:
                print("deleting", okey)
            self.delete(okey)

        if (out := self.get(okey)) is not None:
            if self.verbose:
                print("cache hit", okey)
            return out

        if self.verbose:
            print("cache miss", okey)
        data = self.func(*args_in, **kwargs_in)
        return self.put(okey, data)

    def hash(self, args_in, kwargs_in):
        """Return a hash based on the input args. Default is JSON
        serialization.
        """
        act_args = (
            args_in
            if self.ignore_args is None
            else [arg for ind, arg in enumerate(args_in) if ind not in self.ignore_args]
        )

        # Make sure all known kwargs are part of the hash, not just the ones
        # passed.
        full_kwargs = dict(self.default_kwargs)
        full_kwargs.update(kwargs_in)

        act_kwargs = (
            full_kwargs
            if self.ignore_kwargs is None
            else {k: v for k, v in full_kwargs.items() if k not in self.ignore_kwargs}
        )

        return hashlib.sha512(pickle.dumps([act_args, act_kwargs])).hexdigest()

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

        Only useful when making a direct call.
        """
        raise NotImplementedError
