from setuptools import setup, find_packages


def get_long_description():
    with open("README.md", encoding="utf-8") as file:
        return file.read()


REQUIREMENTS = [
    "aiosqlite",
    "aiohttp",
    "disnake",
]
DOCS = "https://jgltechnologies.com/dpys"
VERSION = "5.3.7"

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
]

setup(
    name="dpys",
    version=VERSION,
    description="A library to simplify discord.py",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url=DOCS,
    author="George Luca",
    author_email="fixingg@gmail.com",
    license="MIT",
    classifiers=classifiers,
    keywords="discord",
    packages=find_packages(),
    install_requires=REQUIREMENTS,
)
