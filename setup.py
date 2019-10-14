from setuptools import setup, find_packages

#####
# setup_tools install info
setup(
    name='h3m',
    version='0.8',
    description='halite match manager',
    author='Tim Olson',
    url='https://gitlab.com/timjolson/halite3-match-manager',
    packages=find_packages(),
    install_requires=['six>=1.11.0', 'tqdm', 'skills'],
    python_requires='>3.0',
)