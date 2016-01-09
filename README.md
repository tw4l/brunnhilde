## Brunnhilde - A companion to Richard Lehane's Seigfried  
(www.itforarchivists.com/siegfried)  

Brunnhilde runs Siegfried against a specified directory, loads the results into a sqlite3 database, and queries the database to generate aggregate reports to aid in triage, arrangement, and description of digital archives.  

Reports:  

1. Sorted format list with count  
2. Sorted format and version list with count  
3. Sorted mimetype list with count  
4. All files with Siegfried errors  
5. All files with Siegfried warnings  
6. All unidentified files  
7. All duplicates (based on Siegfried-generated md5 hash)  

Reports are written as CSV files to a new 'reports' directory created in the directory from which Brunnhilde is run.  

Brunnhilde takes two arguments:  

1. path of directory to scan  
2. basename for reports (e.g. accession number or other identifier)  

'python brunnhilde.py directory basename'  

## Dependencies  

Brunnhilde was written for Python 2.7. It has yet to be tested with Python 3.x but should be (at least mostly) compatible.  

## Licensing  

The MIT License (MIT)  

Copyright (c) 2016 Tim Walsh  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  
