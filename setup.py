from setuptools import find_packages, setup


def get_long_description():
    with open("README.md", encoding="utf-8") as file:
        return file.read()


REQUIREMENTS = [
    "aiosqlite>=0.17,<1",
    "aiohttp>=3.8,<4",
    "disnake>=2.12,<3",
]
DOCS = "https://jgltechnologies.com/dpys"
VERSION = "5.6.5"

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
]

setup(
    name="dpys",
    version=VERSION,
    description="A library to simplify disnake",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url=DOCS,
    author="George Luca",
    author_email="fixingg@gmail.com",
    license="MIT",
    classifiers=classifiers,
    keywords="discord",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=REQUIREMENTS,
    python_requires=">=3.10",
)
