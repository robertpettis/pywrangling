from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.2.3",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'tqdm',
    ],
)
