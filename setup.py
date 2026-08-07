from setuptools import setup, find_packages

setup(
    name="pywrangling",
    version="0.57.0",
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
        'cryptography',
        'pymysql',
        'sqlalchemy',
        'PyJWT',
        'pyodbc',
        'watermark'
    ],
)
