from paver.easy import *
import paver.doctools
from paver.setuputils import setup

setup(
    name="Baudot",
    packages=['baudot'],
    version="0.1",
    url="https://github.com/drupal4media/baudot",
    author="Esteban Sancho",
    author_email="esteban.sancho@gmail.com"
)

@task
@needs('setuptools.command.sdist')
def sdist():
    """Main build"""
    pass
