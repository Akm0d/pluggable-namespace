from pathlib import Path
from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(name="pns._ccontract", sources=["src/pns/_contract.py"]),
    Extension(name="pns._cdata", sources=["src/pns/_data.py"]),
    Extension(name="pns._chub", sources=["src/pns/_hub.py"]),
]

SETUP_DIRNAME = Path(__file__).parent


setup(
    ext_modules=cythonize(extensions),
    include_package_data=True,
)
