'''
  Description of the module here

  :copyright: Copyright 2011 Esteban Sancho
  :license: BSD, see LICENSE for details
'''

from paver.easy import *
from paver.setuputils import setup

# Necessary to run built-in sphinx doc generator
# Since paver is not distributed completely, paver.doctools
# won't be available in all environments.
try:
    import paver.doctools
except ImportError:
    pass

long_description = ''' Baudot is a tool for converting between different
character encodings. It provides two versions:
* Command line
* Rich UI using GTK
'''

# standard setup information
# for more details about the keys, see:
# http://docs.python.org/distutils/setupscript.html
setup(name="Baudot",
    version="0.1",
    license='BSD',
    description='Character encoding tool',
    long_description=long_description,
    author="Esteban Sancho",
    author_email="esteban.sancho@gmail.com",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Command Line',
        'Environment :: Gnome',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Markup :: HTML'
    ],
    url="https://github.com/drupal4media/baudot",
    packages=['baudot'],
    include_package_data=True,
    install_requires = ['PyICU', 'path.py'],#'PyGTK', 'python-magic', 
    test_suite = 'nose.collector',
)

# Used to tell paver where to put the generated html from Sphinx.
options(
    sphinx=Bunch(
        builddir="_build"
    )
)

@task
@needs('minilib','generate_setup', 'distutils.command.sdist')
def sdist():
    '''Generates a standard source distribution. Ensures that minilib and
    setup.py are generated by paver first.
    '''
    pass

@task
def coverage():
    '''Finds and runs all tests. Produces a coverage report on the standard
    output and in html in the cover/ directory. Requires nose and the coverage
    module.
    '''
    command = 'nosetests --with-coverage --cover-package baudot ' + \
              '--cover-html'
    sh(command)

@task
def clean():
    '''Removes all pyc files.
    '''
    d = path(".")
    for f in d.walkfiles('*.pyc'):
        f.remove()
