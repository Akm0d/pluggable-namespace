from pathlib import Path
from setuptools import setup
from setuptools.extension import Extension

try:
    from Cython.Build import cythonize

    HAS_CYTHON = True
except ImportError:
    HAS_CYTHON = False

SETUP_DIRNAME = Path(__file__).parent

requirement_extras = {}
REQUIREMENTS = SETUP_DIRNAME / "requirement"
for req_file in REQUIREMENTS.glob("*.txt"):
    with open(req_file) as f:
        requirement_extras[req_file.stem] = sorted(
            line for line in f.read().splitlines() if line.strip()
        )

requirement_extras["full"] = sum(requirement_extras.values(), [])

kwargs = {}
if HAS_CYTHON:
    extensions = [
        Extension(name="pns._ccontract", sources=["src/pns/_contract.py"]),
        Extension(name="pns._cdata", sources=["src/pns/_data.py"]),
        Extension(name="pns._chub", sources=["src/pns/_hub.py"]),
    ]
    kwargs["ext_modules"] = cythonize(extensions)

setup(extras_require=requirement_extras, include_package_data=True, **kwargs)
