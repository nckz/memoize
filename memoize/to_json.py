"""An abstract class with the framework necessary for function memoization.
Author: Nick Zwart
Date: 2024nov28
"""

# stdlib
import json
import os

# local
from .memoize_api import MemoizeAPI


class ToJSON(MemoizeAPI):
    """An implementation that attempts to cache with python pickle
    serialization.
    """

    def __init__(self, func, cache_prefix="", cache_path="/tmp"):
        super().__init__(func, cache_prefix)
        self._cache_path = cache_path

    def key(self, args_in, kwargs_in):
        """Add the json extension to the superclass key"""
        return super().key(args_in, kwargs_in) + ".json"

    def check(self, fname):
        return os.path.exists(os.path.join(self._cache_path, fname))

    def fetch(self, fname):
        fpath = os.path.join(self._cache_path, fname)
        with open(fpath, "r") as fil:
            return json.load(fil)

    def store(self, fname, data):
        fpath = os.path.join(self._cache_path, fname)
        print("writing to", fpath)
        with open(fpath, "w") as fil:
            json.dump(data, fil)

    def delete(self, fname):
        fpath = os.path.join(self._cache_path, fname)
        os.remove(fpath)
