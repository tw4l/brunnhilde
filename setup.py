from setuptools import setup

setup(
    name = 'brunnhilde',
    version = '1.8.1',
    url = 'https://github.com/timothyryanwalsh/brunnhilde',
    author = 'Tim Walsh',
    author_email = 'timothyryanwalsh@gmail.com',
    py_modules = ['brunnhilde'],
    scripts = ['brunnhilde.py'],
    description = 'A Siegfried-based digital archives reporting tool for directories and disk images',
    keywords = 'archives reporting characterization identification diskimages',
    platforms = ['POSIX', 'Windows'],
    install_requires=['requests'],
    test_suite='test',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Natural Language :: English', 
        'Operating System :: MacOS',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: System :: Archiving',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities'
    ],
)
