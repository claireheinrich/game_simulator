from setuptools import setup

# Read in the requirements.txt file
with open('requirements.txt') as f:
    requirements = []
    for library in f.read().splitlines():
        if "hypothesis" not in library:  # Skip: used only for dev
            requirements.append(library)

# Read in long description
with open("README.rst", "r") as f:
    long_description = f.read()

setup(
    name='Game Simulator',
    install_requires=requirements,
    packages=['gamesimulator', 'gamesimulator.strategies'],
    description='Simulate a two action game theory tournament. Based on the work of Vince Knight, Owen Campbell, and Marc Harper',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3 :: Only',
        ],
    python_requires='>=3.5',
)
