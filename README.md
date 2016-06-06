## Brunnhilde - A companion to Seigfried  

**Please note, this is the development branch of Brunnhilde. Code found in this branch has likely not been tested. For the latest stable release, please consult the master branch.**

Generates aggregate reports of files in a directory based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

Brunnhilde runs Siegfried against a specified directory or disk image, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. Outputs include:  

* A folder of CSV reports on file formats and versions, mimetypes, last modified dates, unidentified files, Siegfried warnings and errors, and duplicate files (by md5 hash)  
* A tree report of the directory structure  
* The full Siegfried CSV output  
* A human-readable HTML report, presenting the information from the CSV outputs in a single place alongside some aggregate statistics about the material as a whole (number of files, number of identified file formats, begin and end dates, number of unique files vs. duplicate files, and so on)  

All outputs are placed into a new directory named after the filename passed to Brunnhilde as the second argument.  

### Running Brunnhilde  

usage: brunnhilde.py [-h] [-d] source filename  

positional arguments:  
* source : Path to source directory or disk image  
* filename : Name of csv file to create  

optional arguments:  
* -h, --help : show this help message and exit  
* -d, --diskimage : Use disk image instead of dir as input   

This new version of Brunnhilde uses SleuthKit's tsk_recover to carve files from disk images for processing. This works with raw (dd) images by default. In Bitcurator or any other environment where libewf has been compiled into SleuthKit, Brunnhilde's -d mode will also support forensic disk image formats, including aff and ewf (E01).  

### Dependencies  

* Python 2.7
* [Siegfried](http://www.itforarchivists.com/siegfried) (any version between 1.0.0 and 1.4.5) must be installed on your machine. Brunnhilde is not yet compatible with Siegfried 1.5.*, which introduces major changes including the ability to use multiple file identification tools.  
* tree (Installed by default in most Linux distros. On OS X, install using [Homebrew](http://brewformulas.org/tree). If tree is not installed on your machine, a blank tree.txt file will be created instead).  
* SleuthKit (brew install sleuthkit)

### Licensing  

The MIT License (MIT)  

Copyright (c) 2016 Tim Walsh  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  
