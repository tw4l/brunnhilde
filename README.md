## Brunnhilde - A reporting companion to Siegfried  

[![Build Status](https://travis-ci.org/timothyryanwalsh/brunnhilde.svg?branch=dev-nohash)](https://travis-ci.org/timothyryanwalsh/brunnhilde)

### Version: Brunnhilde 1.6.0

Generates aggregate reports of files in a directory or disk image based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

For the graphical user interface (GUI) version of Brunnhilde, see [Brunnhilde GUI](https://github.com/timothyryanwalsh/brunnhilde-gui).   

Brunnhilde runs Siegfried against a specified directory or disk image, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. The program will also check for viruses unless specified otherwise, and will optionally run bulk_extractor against the given source. Outputs include:  

* "*basename*.html": Includes some provenance information on the scan itself, aggregate statistics for the material as a whole (number of files, begin and end dates, number of unique vs. duplicate files, etc.), and detailed reports on content found (file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings/errors, duplicate files, and -optionally - potential personal identifiable information found by bulk_extractor). Named after basename passed to Brunnhilde as last argument.  
* "csv_reports" folder: Contains CSV results queried from database on file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings and errors, and duplicate files.  
* "tree.txt": Tree report of the directory structure (of a directory or files within a disk image)
* "siegfried.csv": Full CSV output from Siegfried
* "siegfried.sqlite": SQLite3 database generated from Siegfried CSV  

Optionally, outputs may also include:  

* "bulk_extractor" folder: Contains bulk_extractor outputs (if selected).  
* "carved_files" folder: Contains files carved from disk images by tsk_recover or HFS Explorer (if selected; can be deleted at end of process by passing the '-r' or '--remove files' flag to Brunnhilde).  
* "logs" folder: Contains log files for ClamAV and bulk_extractor (if selected).  

All outputs are placed into a new directory named after the identifier passed to Brunnhilde as the last argument.  

For the most accurate statistics with Siegfried 1.6+, it is advised to force Siegfried to make single identifications for files with multiple filetypes. This can be accomplished with roy using the following command:  

```
roy build -multi 0  
```  

For a more detailed explanation of how multiple identifications are handled by Siegfried, see [https://github.com/richardlehane/siegfried/issues/75](https://github.com/richardlehane/siegfried/issues/75).  

### Installation  

Brunnhilde and all of its dependencies are already installed in BitCurator version 1.7.106+. In versions 1.8.0+, a terminal launcher for Brunnhilde is included in the "Forensics and Reporting" folder on the BitCurator desktop.  

Brunnhilde minimally requires that Python 2 or 3 and Siegfried are installed on your system. For more information, see "Dependencies" below.  

`sudo pip install brunnhilde`  

Once installed, you can call brunnhilde with just `brunnhilde.py [arguments]`.  


### Usage

```  
usage: brunnhilde.py [-h] [-a] [-b] [--ssn_mode SSN_MODE] [-d] [--hfs]
                     [--tsk_imgtype TSK_IMGTYPE] [--tsk_fstype TSK_FSTYPE]
                     [--tsk_sector_offset TSK_SECTOR_OFFSET] [--hash HASH]
                     [-n] [-r] [-t] [-V] [-w] [-z]
                     source destination basename

positional arguments:
  source                Path to source directory or disk image
  destination           Path to destination for reports
  basename              Accession number or identifier, used as basename for
                        outputs

optional arguments:
  -h, --help            show this help message and exit
  -a, --allocated       Instruct tsk_recover to export only allocated files
                        (recovers all files by default)
  -b, --bulkextractor   Run Bulk Extractor on source
  --ssn_mode SSN_MODE   Specify ssn_mode for Bulk Extractor (0, 1, or 2)
  -d, --diskimage       Use disk image instead of dir as input
  --hfs                 Use for raw disk images of HFS disks
  --tsk_imgtype TSK_IMGTYPE
                        Specify format of image type for tsk_recover. See
                        tsk_recover man page for details
  --tsk_fstype TSK_FSTYPE
                        Specify file system type for tsk_recover. See
                        tsk_recover man page for details
  --tsk_sector_offset TSK_SECTOR_OFFSET
                        Sector offset for particular volume for tsk_recover to
                        recover
  --hash HASH           Specify hash algorithm
  -n, --noclam          Skip ClamScan Virus Check
  -r, --removefiles     Delete 'carved_files' directory when done (disk image
                        input only)
  -t, --throttle        Pause for 1s between Siegfried scans
  -V, --version         Display Brunnhilde version
  -w, --showwarnings    Add Siegfried warnings to HTML report
  -z, --scanarchives    Decompress and scan zip, tar, gzip, warc, arc with
                        Siegfried


```  
  
For file paths containing spaces in directory names, enclose the entire path in single or double quotes, or (in versions 1.4.1+) make sure spaces are escaped properly (e.g. `CCA\ Finding\ Aid\ Demo\`).  

In Brunnhilde 1.4.1+, Brunnhilde will accept absolute or relative paths for source and destination.  

Example commands:  
`brunnhilde.py -z "/home/bcadmin/Desktop/Folder to Scan" /home/bcadmin/Desktop brunnhilde-test-0` :  will result in a new directory "brunnhilde-test-0" on the BitCurator desktop containing various reports on input source "Folder to Scan".  

`brunnhilde.py -nz . /Users/twalsh/Desktop/ ARCH123456` : will result in new directory "ARCH123456" on Mac desktop containing various reports on current working directory (-n skips ClamAV virus scan).  

### Virus scanning  

By default, Brunnhilde will use ClamAV to scan the contents of a directory or files in a disk image. Findings are written to a log and to the terminal. If any threats are found, Brunnhilde will print a warning to the terminal and direct the user to the ClamAV log file.  

To disable virus scanning, pass '-n' or'--noclam' as an argument.  

### Siegfried options  

By default, Brunnhilde uses the following Siegfried command:  

```  
sf -csv -hash md5 DIR > CSV  
```  

To enable scanning of archive files (zip, tar, gzip, warc, arc), pass '-z' or '--scanarchives' as an argument.  

To force Siegfried to pause for 1 second between file scans, pass '-t' or '--throttle' as an argument.  

### Specifying hash type  

Brunnhilde uses the md5 hash algorithm by default. Other options are sha1, sha256, sha512, or none.  

To change the type of hash used, pass '--hash HASH' as an argument to Brunnhilde, replacing HASH with your choice of sha1, sha256, or sha512.

If the user specifies not to calculate checksums with '--hash none', the resulting CSV outputs and HTML report will not contain information calculated from hash values, namely information about duplicates in the source.

### Report completeness  

In order to to keep the HTML from being excessively large, Brunnhilde 1.3.0+ no longer includes Siegfried warnings in the HTML report by default (the CSV is still created).  

To include Siegfried warnings in the report, pass '-w' or '--showwarnings' as an argument.

### bulk_extractor  

To enable scanning of files with bulk_extractor, pass '-b' or '--bulkextractor' as arguments. This is disabled by default. Results are written to a 'bulk_extractor' sub-directory. In addition, running bulk_extractor adds a "Personal Identifiable Information (PII)" section to the HTML report to enable quick scanning of these results.  

In Brunnhilde 1.5.1+, specify the ssn_mode passed to bulk_extractor with `--ssn_mode INT`. Valid choices are 0, 1, or 2. If not specified, Brunnhilde will default to 1. See the following explanation of the modes from the [bulkextractor 1.5 release notes](https://github.com/simsong/bulk_extractor/blob/master/doc/announce/announce_1.5.md):

```
SSN recognition: you are now able to specify one of three SSN recognition modes:  

-S ssn_mode=0 SSN’s must be labeled “SSN:”. Dashes or no dashes are okay.  
-S ssn_mode=1 No “SSN” required, but dashes are required.  
-S ssn_mode=2 No dashes required. Allow any 9-digit number that matches SSN allocation range.  
```

### Using disk images as input  

In -d mode, Brunnhilde uses SleuthKit's tsk_recover to export files from a disk image into a "carved files" directory for analysis. This works with raw images by default. In BitCurator or any other environment where libewf has been compiled into SleuthKit, Brunnhilde's -d mode also supports forensic disk image formats, including aff and ewf (E01). Due to the limitations of SleuthKit, Brunnhilde does not yet support characterizing disks that use the UDF filesystem.  

**Note: tsk_recover does not retain file system dates, so the date reporting functionality of Brunnhilde is limited for non-HFS disk images. It is advised to create DFXML or similar files to retain/analyze file system metadata such as date stamps.**

By default, Brunnhilde will keep a copy of the files exported from disk images in a "carved_files" directory. If you do not wish to keep a copy of these files after reporting is finished, you can pass the "-r" or "--removefiles" flags as arguments to Brunnhilde, which will cause it to delete the "carved_files" directory once all other tasks have finished.

Brunnhilde 1.5.3+ includes some options for more granular control of tsk_recover:

-a: Export only allocated files (by default, Brunnhilde passes the -e option to tsk_recover, instructing it to extract all files from disk images, including deleted files, for reporting)  
--tsk_fstype: Specify file system type in image (if not specified, tsk_recover will make best guess; to see possible values, type `tsk_recover -f list` in a terminal)  
--tsk_imgtype: Specify disk image type (if not specified, tsk_recover will make best guess; to see possible values, type `tsk_recover -i list` in a terminal)  
--tsk_sector_offset: Specify which volume on a disk to extract files from based on sector offset (see tsk_recover man page for more details)  

An example command for these values might be:  
`brunnhilde.py -d --tsk_fstype fat --tsk_imgtype ewf --tsk_sector_offset 59 sampleimage.E01 . test0`

### HFS-formatted disk images  

**Important note: unhfs, the command-line version of HFSExplorer, until recently had a bug that prevented some files from being extracted from HFS disks. Be sure that you have the [latest version](https://sourceforge.net/projects/catacombae/files/HFSExplorer/0.23.1%20%28snapshot%202016-09-02%29/) of HFSExplorer installed. In BitCurator 1.7.106+, this issue is fixed in the standard installation.**  

In this patched release, unhfs.sh is renamed to unhfs (without a file extension). If file /usr/share/hfsexplorer/bin/unhfs.sh (with file extension) exists in your system, you must update HFSExplorer with the version linked above.  

In BitCurator versions before 1.7.106, installation of the latest release of HFSEexplorer must be done manually by replacing the contents of /usr/share/hfsexplorer with the downloaded and extracted source. In order to continue using the HFSExplorer GUI in BitCurator versions before 1.7.106 after updating HFSExplorer, right-click on the HFS Explorer icon in "Additional Tools", select "Properties", and amend the text in "Command" to:  

`/usr/share/hfsexplorer/bin/./hfsexplorer %F`   

To characterize HFS formatted disks in Brunnhilde, pass both the "-d" and "--hfs" flags as arguments, and be sure to use a raw disk image as the source (HFSExplorer is unable to process forensically packaged disk images). This functionality works "off the shelf" in BitCurator. Non-BitCurator environments will require you to install additional dependencies (HFSExplorer and Java).  

### Dependencies  

All dependencies are already installed in BitCurator 1.7.106+. See instructions below for installing dependencies if you wish to use Brunnhilde in macOS or a different Linux environment (Brunnhilde is not supported in Windows).  

#### Core requirements
* Python (tested in 2.7 and 3.5)
* [Siegfried](http://www.itforarchivists.com/siegfried): Brunnhilde is now compatible with all version of Siegfried, including 1.6+. It does not support MIME-Info or FDD signatures: for Brunnhilde to work, Siegfried must be using the PRONOM signature file only. If you have been using MIME-Info or FDD signatures as a replacement for or alongside PRONOM with Siegfried 1.5/1.6 on your machine, entering `roy build -multi 0` in the terminal should return you to Siegfried's default PRONOM-only identification mode and allow Brunnhilde to work properly.   

#### Optional  
* [bulk_extractor](https://github.com/simsong/bulk_extractor): Can be built on Linux and OS X from source distribution found [here](https://github.com/simsong/bulk_extractor) or installed using [Homebrew](http://brewformulas.org/BulkExtractor).  
* [ClamAV](https://www.clamav.net): Brunnhilde checks for viruses using ClamAV, which can be built from the source distribution found at [clamav.net](http://clamav.net) or using [Homebrew](http://brewformulas.org/Clamav).   
* tree: Installed by default in most Linux distros. On OS X, install using [Homebrew](http://brewformulas.org/tree). If tree is not installed on your machine, a blank tree.txt file will be created instead.  

#### To process disk images  
* [SleuthKit](http://www.sleuthkit.org/): Install from source or, in OS X, using [Homebrew](http://brewformulas.org/sleuthkit).
* [HFSExplorer](https://sourceforge.net/projects/catacombae/files/HFSExplorer/0.23.1%20%28snapshot%202016-09-02%29/): Install from source.  

### Future development to-dos

* Add ability to use MIME-Info signature files (alone or alongside PRONOM) with Siegfried 1.5+  
* Add ability to use FDD signature files (alone or alongside PRONOM) with Siegfried 1.6+  
* Add support for disk images of DVDs using UDF file system    

### Thanks

Thank you to Richard Lehane for writing Siegfried, Ross Spencer for ideas and help, Kevin Powell for suggesting the additions of ClamAV and bulk_extractor and writing the initial code to integrate these tools, and to the PRONOM team at the UK National Archives for building and maintaining such a wonderful tool.  

### Licensing  

The MIT License (MIT)  
Copyright (c) 2017 Tim Walsh
