"""
SNAPsynth: KATCP-based controller for the SNAP board's synth.
"""
from distutils.core import setup

if __name__ == '__main__':
    setup(name = 'SNAPsynth',
        description = __doc__,
        long_description = __doc__,
        license = 'GPL',
        author = 'Rachel Simone Domagalski',
        author_email = 'domagalski@berkeley.edu',
        url = 'https://github.com/domagalski/snap-synth',
        package_dir = {'':'src'},
        py_modules = ['SNAPsynth'],
    )
