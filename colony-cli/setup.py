import os

from setuptools import find_packages, setup

with open(os.path.join("../version.txt")) as version_file:
    version_from_file = version_file.read().strip()

with open("../requirements.txt") as f_required:
    required = f_required.read().splitlines()

with open(os.path.join("../colony-cli/README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="colony-cli",
    version=version_from_file,
    packages=find_packages(where="..", exclude=["*.tests", "*.tests.*", "tests.*", "tests", "torque-cli"]),
    package_dir={"": ".."},
    url="https://www.quali.com/",
    license="Apache Software License",
    author="Quali",
    author_email="support@qualisystems.com",
    description="A command line interface for colony",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: User Interfaces",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    entry_points={"console_scripts": ["colony=colony.shell:main_colony"]},
    install_requires=required,
    keywords="colony sandbox cloud cloudshell quali command-line cli",
    python_requires=">=3.6",
)
