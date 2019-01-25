from setuptools import setup, find_packages

setup(
    name="ctapipe_magic",
    packages=find_packages(),
    version="0.0.1",
    description="Module to analyze MAGIC data with ctapipe",
    install_requires=[
        "uproot",
        "ctapipe",
        "ctapipe-extra",
    ],
    tests_require=[
        "pytest",
        "ctapipe-extra>=0.2.11",
    ],
    author="Noah Biederbeck",
    author_email="noah.biederbeck@tu-dortmund.de",
    license="mit",
    url="https://github.com/tudo-astroparticlephysics/ctapipe_magic",
    zip_safe=False,
)
