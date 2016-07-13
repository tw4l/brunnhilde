## Brunnhilde - A companion to Seigfried  

Generates aggregate reports of files in a directory based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

Brunnhilde runs Siegfried against a specified directory or disk image, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. Outputs include:  

* A folder of CSV reports on file formats and versions, mimetypes, last modified dates, unidentified files, Siegfried warnings and errors, and duplicate files (by md5 hash)  
* An HTML report which includes some provenance information on the scan itself, aggregate statistics for the material as a whole (number of files, begin and end dates, number of unique vs. duplicate files, etc.), and all non-blank CSV reports printed as HTML tables
* A tree report of the directory structure  
* The full Siegfried CSV output  

All outputs are placed into a new directory named after the filename passed to Brunnhilde as the last argument.  

### Running Brunnhilde  

usage: brunnhilde.py [-h] [-d] [--hfs] [-r] source filename  

positional arguments:  
  source : Path to source directory or disk image  
  filename : Name of csv file to create  

optional arguments:  
  -h, --help : show this help message and exit  
  -d, --diskimage : Use disk image instead of dir as input  
  --hfs : Use for raw disk images of HFS disks  
  -r, --removefiles : Delete 'carved_files' directory when done  

### Using disk images as input  

In -d mode, Brunnhilde uses SleuthKit's tsk_recover to export files from a disk image into a "carved files" directory for analysis. This works with raw (dd) images by default. In Bitcurator or any other environment where libewf has been compiled into SleuthKit, Brunnhilde's -d mode also supports forensic disk image formats, including aff and ewf (E01). Due to the limitations of SleuthKit, Brunnhilde does not yet support characterizing disks that use the UDF filesystem.  

To characterize HFS formatted disks, use both the "-d" and "--hfs" flags, and be sure to use a raw disk image as the source (HFSExplorer is unable to process forensically packaged disk images). This functionality works best in Bitcurator. Non-Bitcurator environments will require you to install additional dependencies (HFSExplorer and Java) and to configure some Brunnhilde settings, such as the path to the "unhfs.sh" script and potentially the options being passed to it.  

By default, Brunnhilde will keep a copy of the files exported from disk images in a "carved_files" directory. If you do not wish to keep a copy of these files after reporting is finished, you can pass the "-r" or "--removefiles" flag to have Brunnhilde delete the directory when it is finished.  

### Dependencies  

#### General  
* Python 2.7
* [Siegfried](http://www.itforarchivists.com/siegfried): Brunnhilde is now compatible with all version of Siegfried, including 1.6.1. It does not yet have support for MIME-Info or FDD signatures: for Brunnhilde to work, Siegfried must be using the PRONOM signature file only. If you have been using MIME-Info or FDD signatures as a replacement for or alongside PRONOM with Siegfried 1.5/1.6 on your machine, entering "roy build" in the terminal should return you to Siegfried's default PRONOM-only identification mode and allow Brunnhilde to work properly.  
* tree: Installed by default in most Linux distros. On OS X, install using [Homebrew](http://brewformulas.org/tree). If tree is not installed on your machine, a blank tree.txt file will be created instead.  

#### To process disk images  
* [SleuthKit](http://www.sleuthkit.org/): Installed by default in Bitcurator. On OS X, can be installed using Homebrew with "brew install sleuthkit".
* [HFSExplorer](http://www.catacombae.org/hfsexplorer/): Installed by default in Bitcurator. Brunnhilde uses unhfs, the included command-line implementation of HFSExplorer.  

### Future development to-dos

* Add ability to use MIME-Info signature files (alone or alongside PRONOM) with Siegfried 1.5.0  
* Add support for UDF disk images  
* More and better testing  
* Move from raw SQL to ORM?  

### Licensing  

The MIT License (MIT)  

Copyright (c) 2016 Tim Walsh  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  
