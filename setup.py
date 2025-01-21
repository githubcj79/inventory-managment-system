# setup.py
from setuptools import setup, find_packages

setup(
    name="inventory-management-system",
    version="0.1",
    packages=find_packages(include=['services', 'services.*']),
    install_requires=[
        'pymongo[srv]>=4.6.1',
        'python-dotenv>=1.0.0',
        'structlog>=23.2.0',
    ],
)
