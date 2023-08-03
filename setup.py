from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.3.0",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'tqdm',
        'geopandas',
        'geopy',
        'googlemaps',
        'matplotlib',
    ],
)
