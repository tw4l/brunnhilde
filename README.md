## Brunnhilde - A reporting companion to Siegfried  

### Version: Brunnhilde v1.1.0

Generates aggregate reports of files in a directory or disk image based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

For the graphical user interface (GUI) version of Brunnhilde, see: https://github.com/timothyryanwalsh/brunnhildegui  

Brunnhilde runs Siegfried against a specified directory or disk image, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. The program will also check for viruses unless specified otherwise, and will optionally run bulk_extractor against the given source. Outputs include:  

* "*basename*.html": Includes some provenance information on the scan itself, aggregate statistics for the material as a whole (number of files, begin and end dates, number of unique vs. duplicate files, etc.), and detailed reports on content found (file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings, Siegfried errors, duplicate files, and -optionally - potential personal identifiable information found by bulk_extractor). Named after basename passed to Brunnhilde as last argument.  
* "bulk_extractor" folder: Contains bulk_extractor outputs (if selected).  
* "carved_files" folder: Contains files carved from disk images by tsk_recover or HFS Explorer (if selected; can be deleted at end of process by passing the '-r' or '--remove files' flag to Brunnhilde).  
* "csv_reports" folder: Contains CSV results queried from database on file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings and errors, and duplicate files.  
* "logs" folder: Contains log files for ClamAV and bulk_extractor (if selected).  
* "tree.txt": Tree report of the directory structure (of a directory or files within a disk image)
* "siegfried.csv": Full CSV output from Siegfried
* "siegfried.sqlite": SQLite3 database generated from Siegfried CSV

All outputs are placed into a new directory named after the identifier passed to Brunnhilde as the last argument.  

For the most accurate statistics with Siegfried 1.6+, it is advised to force Siegfried to make single identifications for files with multiple filetypes. This can be accomplished with roy using the following command:  

```
roy build -multi 0  
```  

For a more detailed explanation of how multiple identifications are handled by Siegfried, see [https://github.com/richardlehane/siegfried/issues/75](https://github.com/richardlehane/siegfried/issues/75).  

### Installation  

Download tar.gz or .zip from Brunnhilde repository and extract to location of your choice.  

### Running Brunnhilde  

```  
usage: brunnhilde.py [-h] [-b] [-d] [--hfs] [-n] [-r] [-t] [-v] [-z]
                     source destination basename

positional arguments:
  source               Path to source directory or disk image
  destination          Path to destination for reports
  basename             Accession number or identifier, used as basename for
                       outputs

optional arguments:
  -h, --help           show this help message and exit
  -b, --bulkextractor  Run Bulk Extractor on source
  -d, --diskimage      Use disk image instead of dir as input
  --hfs                Use for raw disk images of HFS disks
  -n, --noclam         Skip ClamScan Virus Check
  -r, --removefiles    Delete 'carved_files' directory when done (disk image
                       input only)
  -t, --throttle       Pause for 1s between Siegfried scans
  -v, --version        Display Brunnhilde version
  -z, --scanarchives   Decompress and scan zip, tar, gzip, warc, arc with
                       Siegfried
```  
  
For file paths containing spaces in directory names, enclose the entire path in '' or "" quotes.  

### Virus scanning  

By default, Brunnhilde will use ClamAV to scan the contents of a directory or files in a disk image. Findings are written to a log and to the terminal. If any threats are found, Brunnhilde will prompt the user to indicate whether they wish to continue processing the files.  

To disable virus scanning, pass '-n' or'--noclam' as arguments to Brunnhilde.  

### Siegfried options  

By default, Brunnhilde v1.1.0 uses the following Siegfried command:  

```  
sf -csv -hash md5 DIR > CSV  
```  

To enable scanning of archive files (zip, tar, gzip, warc, arc), pass '-z' or '--scanarchives' as arguments to Brunnhilde.  

To force Siegfried to pause for 1 second between file scans, pass '-t' or '--throttle' as arguments to Brunnhilde.  

### bulk_extractor  

To enable scanning of files with bulk_extractor, pass '-b' or '--bulkextractor' as arguments. This is disabled by default. Results are written to a 'bulk_extractor' sub-directory. In addition, running bulk_extractor adds a "Personal Identifiable Information (PII)" section to the HTML report to enable quick scanning of these results.  

### Using disk images as input  

In -d mode, Brunnhilde uses SleuthKit's tsk_recover to export files from a disk image into a "carved files" directory for analysis. This works with raw images by default. In Bitcurator or any other environment where libewf has been compiled into SleuthKit, Brunnhilde's -d mode also supports forensic disk image formats, including aff and ewf (E01). Due to the limitations of SleuthKit, Brunnhilde does not yet support characterizing disks that use the UDF filesystem.  

To characterize HFS formatted disks, pass both the "-d" and "--hfs" flags as arguments to Brunnhilde, and be sure to use a raw disk image as the source (HFSExplorer is unable to process forensically packaged disk images). This functionality works best in Bitcurator. Non-Bitcurator environments will require you to install additional dependencies (HFSExplorer and Java) and to configure some Brunnhilde settings, such as the path to the "unhfs.sh" script and potentially the options being passed to it.  

By default, Brunnhilde will keep a copy of the files exported from disk images in a "carved_files" directory. If you do not wish to keep a copy of these files after reporting is finished, you can pass the "-r" or "--removefiles" flags as arguments to Brunnhilde, which will cause it to delete the "carved_files" directory once all other tasks have finished.    

### Dependencies  

All dependencies are already installed in Bitcurator. See instructions below for installing dependencies if you wish to use Brunnhilde in OS X or a different Linux environment.  

#### General  
* Python 2.7
* [Siegfried](http://www.itforarchivists.com/siegfried): Brunnhilde is now compatible with all version of Siegfried, including 1.6.1. It does not yet have support for MIME-Info or FDD signatures: for Brunnhilde to work, Siegfried must be using the PRONOM signature file only. If you have been using MIME-Info or FDD signatures as a replacement for or alongside PRONOM with Siegfried 1.5/1.6 on your machine, entering "roy build" in the terminal should return you to Siegfried's default PRONOM-only identification mode and allow Brunnhilde to work properly.  
* tree: Installed by default in most Linux distros. On OS X, install using [Homebrew](http://brewformulas.org/tree). If tree is not installed on your machine, a blank tree.txt file will be created instead.  
* [bulk_extractor](https://github.com/simsong/bulk_extractor): Can be built on Linux and OS X from source distribution found [here](https://github.com/simsong/bulk_extractor) or installed using [Homebrew](http://brewformulas.org/BulkExtractor).  
* [ClamAV](https://www.clamav.net): Brunnhilde checks for viruses using ClamAV, which can be built from the source distribution found at [clamav.net](http://clamav.net) or using [Homebrew](http://brewformulas.org/Clamav).   

#### To process disk images  
* [SleuthKit](http://www.sleuthkit.org/): Install from source or, in OS X, using [Homebrew](http://brewformulas.org/sleuthkit).
* [HFSExplorer](http://www.catacombae.org/hfsexplorer/): Install from source.  

### Future development to-dos

* Add ability to use MIME-Info signature files (alone or alongside PRONOM) with Siegfried 1.5+  
* Add ability to use FDD signature files (alone or alongside PRONOM) with Siegfried 1.6+  
* Add support for disk images of DVDs using UDF file system    

### Thanks

Thank you to Richard Lehane for writing Siegfried, Ross Spencer for ideas and help, Kevin Powell for suggesting the additions of ClamAV and bulk_extractor and writing the initial code to integrate these tools, and to the PRONOM team at the UK National Archives for building and maintaining such a wonderful tool.  

### Licensing  

The MIT License (MIT)  

Copyright (c) 2016 Tim Walsh  

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:  

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.  

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.  
