"""
snakes - Dynamic snakefile generator for data integration and machine learning pipelines
"""
DOCLINES = __doc__.split("\n")

from setuptools import setup, find_packages

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: MacOS'
]

setup(
    author="Keith Hughitt",
    author_email="keith.hughitt@nih.gov",
    classifiers=CLASSIFIERS,
    description="Dynamic snakefile generator for data integration and machine learning pipelines",
    install_requires=['jinja2', 'PyYAML', 'setuptools-git'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest>=3.0'],
    include_package_data=True,
    license="BSD",
    maintainer="V. Keith Hughitt",
    maintainer_email="keith.hughitt@nih.gov",
    name="snakes",
    packages=find_packages(),
    platforms=["Linux", "Solaris", "Mac OS-X", "Unix", "Windows"],
    provides=['snakes'],
    scripts=['bin/snakes'],
    zip_safe=False,
    url="https://github.com/khughitt/snakes",
    version="0.1"
)
