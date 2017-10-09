from setuptools import setup, find_packages
setup(
    name="Jamberry Unofficial API",
    version="0.2.0.1",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    author='Steven James',
    author_email='steven@waitforitjames.com',
    description='Access your own Jamberry consultant data via python',
    license='MIT',
    keywords='jamberry api',
    install_requires=['mechanicalsoup', 'beautifulsoup4', 'python-dateutil'],
    tests_require=['pytest'],
)
