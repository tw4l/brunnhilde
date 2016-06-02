## Brunnhilde - A companion to Seigfried  

Generates aggregate reports of files in a directory based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

Brunnhilde runs Siegfried against a specified directory, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. Outputs include:  

* A human-readable HTML report  
* A tree report of the directory structure  
* The full Siegfried CSV output  
* A folder of more focused CSV reports on file formats and versions, mimetypes, last modified dates, unidentified files, Siegfried warnings and errors, and duplicate files (by md5 hash).  

All outputs are placed into a new directory named after the filename passed to Brunnhilde as the second argument.  

### Running Brunnhilde  

Brunnhilde takes two arguments:  

1. path of directory to scan  
2. csv output filename (recommended practice: use accession number or other identifier)  

'python brunnhilde.py directory filename.csv'  

### Dependencies  

* Python 2.7
* [Siegfried](http://www.itforarchivists.com/siegfried) (any version between 1.0.0 and 1.4.5) must be installed on your machine. Brunnhilde is not yet compatible with Siegfried 1.5.*, which introduces major changes including the ability to use multiple file identification tools.  
* tree (Installed by default in most Linux distros. On OS X, install using [Homebrew](http://brewformulas.org/tree). If tree is not installed on your machine, a blank tree.txt file will be created instead).  

### Licensing  

The MIT License (MIT)  

Copyright (c) 2016 Tim Walsh  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  
