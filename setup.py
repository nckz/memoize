"""
Brief: pip module description.

Author: Nick Zwart
Date: 2024nov24
"""

from setuptools import setup, find_packages

MODULE_NAME = "memoize"
REQUIRED_PIP_MODULES = None

setup(
    name=MODULE_NAME,
    packages=find_packages(where=".", exclude=["test"]),
    use_scm_version=True,
    install_requires=REQUIRED_PIP_MODULES,
    package_data={"": ["*.yml", "*.txt", "*.ini"]},
)
