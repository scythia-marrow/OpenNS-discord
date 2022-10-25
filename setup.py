from setuptools import setup, find_packages
import pathlib

#here = pathlib.Path(__file__).parent.resolve()

if __name__ == "__main__":
	setup(
		name = "OpenNS-discord",
		description = 'An open-source nationstates discord bot',
		python_requires = ">=3.8, <4",
		package_dir={"": "src"},
		packages = find_packages(
			where="src",
			include=["openNS*"])
	)
