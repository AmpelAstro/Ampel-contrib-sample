from setuptools import setup, find_namespace_packages

setup(
	name='ampel-contrib-sample',
	version='0.7.0',
	packages=find_namespace_packages(),
	package_data = {
		'': ['*.json'], # include any package containing *.json files
		'conf': [
			'*.json', '**/*.json', '**/**/*.json',
			'*.yaml', '**/*.yaml', '**/**/*.yaml',
			'*.yml', '**/*.yml', '**/**/*.yml'
		]
	}
)