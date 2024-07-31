from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="syphoon",
    version="0.0.1",
    author="ZyneLabs",
    author_email=" ",
    description="A Python wrapper for the Syphoon API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=" ",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[
        "requests",
    ],
)
