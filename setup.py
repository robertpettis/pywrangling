from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.36.1.1",
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
        'selenium-wire',
        'boto3',
        'pymysql',
        'sqlalchemy',
        'PyJWT'
    ],
)
