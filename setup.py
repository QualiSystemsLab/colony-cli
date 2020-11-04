from setuptools import setup

setup(
    name='colony-cli',
    version='1.0.0',
    packages=['colony'],
    url='https://www.quali.com/',
    license='Apache Software License',
    author='Quali',
    author_email='support@qualisystems.com',
    description='A command line interface for colony',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: User Interfaces',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
    ],
    entry_points={
        'console_scripts': [
            'colony=colony:main',
        ],
    },
)
