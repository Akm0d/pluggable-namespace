from pathlib import Path
from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(name="pns.contract", sources=["src/pns/contract.pyx"]),
    Extension(name="pns.data", sources=["src/pns/data.pyx"]),
]

SETUP_DIRNAME = Path(__file__).parent


setup(
    ext_modules=cythonize(extensions),
    include_package_data=True,
)
