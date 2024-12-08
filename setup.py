# File: setup.py
from setuptools import setup, find_packages

setup(
    name='book_manager',
    author='Wyatt Roersma',
    author_email='wyattroersma@gmail.com',
    description='A tool to manage book projects, analyze content, and generate compilations',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ThreatFlux/BookManager',
    packages=find_packages(),
    include_package_data=True,
    python_requires='>=3.8',
    setup_requires=['setuptools_scm'],
    use_scm_version={
        'write_to': 'book_manager/_version.py',
    },
    install_requires=[
        'pyyaml>=6.0',
        'tqdm>=4.65.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'black>=22.0.0',
            'pylint>=2.15.0',
            'build>=0.10.0',
            'twine>=4.0.0',
            'setuptools>=45',
            'setuptools_scm>=6.2',
            'wheel>=0.37.0',
            'psutil>=5.9.0',  # Added for performance testing
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'psutil>=5.9.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'book_manager=book_manager.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)