from pathlib import Path
from setuptools import setup
from setuptools import find_packages


HERE = Path(__file__).absolute().parent

with (HERE / 'README.rst').open() as f:
    README = f.read()

with (HERE / 'requirements' / 'minimal.txt').open() as f:
    rows = f.read().strip().split('\n')
    requires = []
    for row in rows:
        row = row.strip()
        if row and not (row.startswith('#') or row.startswith('https')):
            requires.append(row)


# Setup
# ----------------------------

setup(name='graphql-dsl',
      version='0.2.1',
      description='Compose GraphQL queries by composing Python types!',
      long_description=README,
      classifiers=[
          'Development Status :: 1 - Planning',
          'Intended Audience :: Developers',
          'License :: OSI Approved',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Operating System :: POSIX',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Code Generators',
          'Typing :: Typed',
      ],
      author='Maxim Avanov',
      author_email='maxim.avanov@gmail.com',
      url='https://maximavanov.com/',
      project_urls={
          'Documentation': 'https://graphql-dsl.rtfd.io/',
          'Source': 'https://github.com/avanov/graphql-dsl',
      },
      keywords='web',
      packages=find_packages(exclude=['tests', 'tests.*']),
      include_package_data=True,
      zip_safe=False,
      test_suite='tests',
      tests_require=['pytest', 'coverage'],
      install_requires=requires,
      entry_points={
          'console_scripts': [
              'graphql-dsl = graphql_dsl.cli:main'
          ],
      }
    )
