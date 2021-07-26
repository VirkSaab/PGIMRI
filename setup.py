from setuptools import setup, find_packages


def read_requirements():
    with open('requirements.txt', 'r') as req:
        content = req.read()
        requirements = content.split('\n')

    return requirements


setup(
    name='pgimri',
    version='0.0.1',
    packages=find_packages(),
    include_package_date=True,
    install_requires=read_requirements(),
    entry_points="""
        [console_scripts]
        pgimri=pgimri.cli:cli
        dtip=pgimri.dtip.cli:cli
        dkip=pgimri.dkip.cli:cli
    """,
)