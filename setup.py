from setuptools import setup, find_packages

# Read in requirements.txt
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="pywrangling",
    version="0.11",
    packages=find_packages(),
    install_requires=requirements,
)
