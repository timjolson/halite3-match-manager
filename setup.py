from setuptools import setup, find_packages

#####
# setup_tools install info
setup(
    name='halite',
    version='0.5',
    description='halite match manager',
    author='Tim Olson',
    author_email='tim.lsn@gmail.com',
    packages=find_packages(),
    install_requires=['six==1.11.0', 'trueskill==0.4.4', 'zstd==1.3.4.4', 'tqdm', 'skills']
)