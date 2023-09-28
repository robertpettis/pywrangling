from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.8.5.1",
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'tqdm',
        'geopandas',
        'geopy',
        'googlemaps',
        'matplotlib',
        'openai',
        'scipy',
        'selenium',
        'boto3'
    ],
)
