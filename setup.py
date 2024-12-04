from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

# Define Cython extensions
extensions = [
    Extension(name="pns.contract", sources=["src/pns/contract.pyx"]),
    Extension(name="pns.data", sources=["src/pns/data.pyx"]),
]

# Call setup function
setup(
    ext_modules=cythonize(extensions),
)

# TODO calculate "full" dependencies and also gather dependencies dynamically from what imports are used in config.yamls
# Also have extras based on each subproject name
