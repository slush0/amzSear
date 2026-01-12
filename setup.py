from setuptools import setup, find_packages

setup(
    name='amzsear',
    packages=find_packages(),
    version='3.0.1',
    description='The unofficial Amazon search CLI & Python API',
    author="Asher Silvers",
    author_email="ashersilvers@gmail.com",
    license='MIT',
    url='https://github.com/asherAgs/amzSear',
    keywords='amazon search product products python',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    entry_points={
        'console_scripts': [
            'amzsear = amzsear.cli.cli:run',
        ],
    },
    install_requires=[
        "lxml>=4.9.1",
        "cssselect>=1.1.0",
        "lxml_html_clean>=0.1.0",
        "requests>=2.20.0",
    ],
)
