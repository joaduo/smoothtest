
from setuptools import setup, find_packages

name = 'smoothtest'

reqs = '''rel_imp
watchdog
selenium
importlib'''.splitlines()

def long_description():
    with open('README', 'r') as f:
        return unicode(f.read())

setup(
  name = name,
  packages = find_packages(),
  version = '0.1.4',
  description = 'General purpose Testing Utilities and also special testing tools for for Web Applications',
  long_description=long_description(),
  author = 'Joaquin Duo',
  author_email = 'joaduo@gmail.com',
  license='MIT',
  url = 'https://github.com/joaduo/'+name,
  keywords = ['testing', 'automation', 'web', 'unittest'],
  install_requires=reqs,
)
