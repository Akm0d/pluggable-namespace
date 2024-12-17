from pathlib import Path
from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(name="pns.ccontract", sources=["src/pns/contract.py"]),
    Extension(name="pns.cdata", sources=["src/pns/data.py"]),
]

SETUP_DIRNAME = Path(__file__).parent


setup(
    ext_modules=cythonize(extensions),
    include_package_data=True,
)
