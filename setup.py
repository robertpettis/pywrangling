from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'inspec',
        'tqdm',
    ],
)
