from setuptools import setup
setup(name='Ampel-contrib-sample',
      version='0.5.0',
      package_data = {'': ['*.json']},
      packages=[
          'ampel.contrib.groupname.t2',
      ],
)