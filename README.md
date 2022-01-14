## Brunnhilde - Siegfried-based characterization tool for directories and disk images

### Version: Brunnhilde 1.9.3

Generates aggregate reports of files in a directory or disk image based on input from Richard Lehane's [Siegfried](http://www.itforarchivists.com/siegfried).  

For the graphical user interface (GUI) version of Brunnhilde, see [Brunnhilde GUI](https://github.com/tw4l/brunnhilde-gui).   

Brunnhilde runs Siegfried against a specified directory or disk image, loads the results into a sqlite3 database, and queries the database to generate reports to aid in triage, arrangement, and description of digital archives. The program will also check for viruses unless specified otherwise, and will optionally run bulk_extractor against the given source. Outputs include:  

* `report.html`: Includes some provenance information on the scan itself, aggregate statistics for the material as a whole (number of files, begin and end dates, number of unique vs. duplicate files, etc.), and detailed reports on content found (file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings/errors, duplicate files, and -optionally - Social Security Numbers found by bulk_extractor).
* `csv_reports` folder: Contains CSV results queried from database on file formats, file format versions, MIME types, last modified dates by year, unidentified files, Siegfried warnings and errors, and duplicate files.  
* `siegfried.csv`: Full CSV output from Siegfried  

Optionally, outputs may also include:  

* `tree.txt`: Tree report of the directory structure of directory or file system on disk image (in Linux and macOS only)  
* `bulk_extractor` folder: Contains bulk_extractor outputs (if selected).  
* `carved_files` folder: Contains files carved from disk images by tsk_recover or HFS Explorer (generated in `-d` mode; can be deleted at end of process by passing the `-r` or `--removefiles` flag to Brunnhilde).  
* `dfxml.xml`: A fiwalk-generated [Digital Forensics XML](http://www.forensicswiki.org/wiki/Category:Digital_Forensics_XML) file describing the volumes, filesystems, and files on a disk (generated in -d mode for non-HFS disk images).  
* `logs` folder: Contains log files for ClamAV and bulk_extractor (if selected).  
* `siegfried.sqlite`: SQLite3 database generated from Siegfried CSV (deleted at end of processing by default, but may be retained by using the `-k` flag.)

All outputs are placed into a new directory named after the identifier passed to Brunnhilde as the last argument.  

For the most accurate statistics with Siegfried 1.6+, it is advised to force Siegfried to make single identifications for files with multiple filetypes. This can be accomplished with roy using the following command:  

```
roy build -multi 0  
```  

For a more detailed explanation of how multiple identifications are handled by Siegfried, see [https://github.com/richardlehane/siegfried/issues/75](https://github.com/richardlehane/siegfried/issues/75).  

### Installation  

Brunnhilde and all of its dependencies are already installed in BitCurator version 1.7.106+. In versions 1.8.0+, a terminal launcher for Brunnhilde is included in the "Forensics and Reporting" folder on the BitCurator desktop.  

Brunnhilde minimally requires that Python 2 or 3 and Siegfried are installed on your system to characterize directories of content. Characterizing disk images introduces additional dependencies. For more information, see [Dependencies](https://github.com/tw4l/brunnhilde#dependencies).  

`sudo pip install brunnhilde`

If using macOS, you may have to run `sudo pip3 install brunnhilde`

Once installed, you can call brunnhilde with just `brunnhilde.py [arguments]`.  

If an older version of Brunnhilde is installed on your system, you can upgrade to the latest version with:  

`sudo pip install brunnhilde --upgrade`  


### Usage

```  
usage: brunnhilde.py [-h] [-a] [-b] [--ssn_mode SSN_MODE] [--regex REGEX] [-d]
                     [--hfs] [--hfs_resforks] [--hfs_partition HFS_PARTITION]
                     [--hfs_fsroot HFS_FSROOT] [--tsk_imgtype TSK_IMGTYPE]
                     [--tsk_fstype TSK_FSTYPE]
                     [--tsk_sector_offset TSK_SECTOR_OFFSET] [--hash HASH]
                     [-k] [-l] [-n] [-r] [-t] [-v] [-V] [-w] [-z]
                     [--save_assets SAVE_ASSETS] [--load_assets LOAD_ASSETS]
                     [--csv CSV] [--stdin] [-o] [--in-memory-db]
                     source destination [basename]

positional arguments:
  source                Path to source directory or disk image
  destination           Path to destination for reports
  basename              DEPRECATED. Accession number or identifier, used as
                        basename for outputs. Prefer using the new simpler
                        `brunnhilde.py source destination` syntax. The
                        basename argument is retained for API stability and
                        used when provided.

optional arguments:
  -h, --help            show this help message and exit
  -a, --allocated       Instruct tsk_recover to export only allocated files
                        (recovers all files by default)
  -b, --bulkextractor   Run Bulk Extractor on source
  --ssn_mode SSN_MODE   Specify ssn_mode for Bulk Extractor (0, 1, or 2)
  --regex REGEX         Specify path to regex file
  -d, --diskimage       Use disk image instead of dir as input (Linux and
                        macOS only)
  --hfs                 Use for raw disk images of HFS disks
  --hfs_resforks, --resforks
                        HFS option: Extract AppleDouble resource forks from
                        HFS disks
  --hfs_partition HFS_PARTITION
                        HFS option: Specify partition number as integer for
                        unhfs to extract (e.g. --hfs_partition 1)
  --hfs_fsroot HFS_FSROOT
                        HFS option: Specify POSIX path (file or dir) in the
                        HFS file system for unhfs to extract (e.g.
                        --hfs_fsroot /Users/tessa/backup/)
  --tsk_imgtype TSK_IMGTYPE
                        TSK option: Specify format of image type for
                        tsk_recover. See tsk_recover man page for details
  --tsk_fstype TSK_FSTYPE
                        TSK option: Specify file system type for tsk_recover.
                        See tsk_recover man page for details
  --tsk_sector_offset TSK_SECTOR_OFFSET
                        TSK option: Sector offset for particular volume for
                        tsk_recover to recover
  --hash HASH           Specify hash algorithm
  -k, --keepsqlite      Retain Brunnhilde-generated sqlite db after processing
  -l, --largefiles      Enable virus scanning of large files
  -n, --noclam          Skip ClamAV virus scan
  -r, --removefiles     Delete 'carved_files' directory when done (disk image
                        input only)
  -t, --throttle        Pause for 1s between Siegfried scans
  -v, --verbosesf       Log verbose Siegfried output to terminal while
                        processing
  -V, --version         Display Brunnhilde version
  -w, --warnings, --showwarnings
                        Add Siegfried warnings to HTML report
  -z, --scanarchives    Decompress and scan zip, tar, gzip, warc, arc with
                        Siegfried
  --save_assets SAVE_ASSETS
                        DEPRECATED. Non-functional in Brunnhilde 1.9.1+ but
                        retained for API stability
  --load_assets LOAD_ASSETS
                        DEPRECATED. Non-functional in Brunnhilde 1.9.1+ but
                        retained for API stability
  --csv CSV             Path to Siegfried CSV file to read as input
                        (directories only)
  --stdin               Read Siegfried CSV from piped stdin (directories only)
  -o, --overwrite       Overwrite reports directory if it already exists
  --in-memory-db        Use in-memory sqlite database rather than writing it
                        to disk
```  
  
For file paths containing spaces in directory names, enclose the entire path in single or double quotes or make sure spaces are escaped properly (e.g. `CCA\ Finding\ Aid\ Demo\`).  

Brunnhilde will accept absolute or relative paths for source and destination.  

Example commands:

#### Brunnhilde 1.9+

Brunnhilde 1.9.0 introduces a simpler CLI syntax:

`brunnhilde.py /directory/to/scan /output/directory/to/create`

Or with options:

`brunnhilde.py -ndz /home/user/diskimage.dd output_directory` - *scan a disk image (-d), skip the clamav virus check (-n), and instruct Siegfried to scan the contents of zip, tar, gzip, warc, and arc archive files (-z)*

`sf -csv . | brunnhilde.py --stdin . output_directory` - *read a Siegfried CSV report of current directory from piped stdin*

`brunnhilde.py --csv /path/to/existing/siegfried.csv source_directory output_directory` - *read a Siegfried CSV report of source_directory from a file*

The old way of calling Brunnhilde is officially deprecated but will continue to be supported for API stability:

#### Brunnhilde 1.8 and below

`brunnhilde.py /path/to/directory/to/scan /path/to/outputs/directory name_of_output_dir`

Some examples:

`brunnhilde.py -z "/home/bcadmin/Desktop/Folder to Scan" /home/bcadmin/Desktop brunnhilde-test-0` - *results in a new directory "brunnhilde-test-0" on the BitCurator desktop containing various reports on input source "Folder to Scan".* 

`brunnhilde.py -nz . /Users/twalsh/Desktop/ARCH123456` - *results in new directory "ARCH123456" on Mac desktop containing various reports on current working directory (-n skips ClamAV virus scan).*

### SQLite database

By default, Brunnhilde will write a sqlite database to the output directory. To instead have Brunnhilde create and use an in-memory database in RAM, pass `--in-memory-db`.

### Virus scanning

By default, Brunnhilde will use ClamAV to scan the contents of a directory or files in a disk image. Findings are written to a log and to the terminal. If any threats are found, Brunnhilde will print a warning to the terminal and direct the user to the ClamAV log file.  

By default, the maximum filesize and scansize for ClamAV are limited. To enable scanning of large files and large numbers of files, pass `--largefiles` as an argument. This will enable scans of unlimited size and scanning of files up to 4GB (files larger than 4GB are not supported by clamscan).

To disable virus scanning, pass `-n` or `--noclam` as an argument. Virus scanning is skipped in Windows regardless of the options passed to Brunnhilde.

### Siegfried options  

By default, Brunnhilde uses the following Siegfried command:  

```  
sf -csv -hash md5 DIR > CSV  
```  

To enable scanning of archive files (zip, tar, gzip, warc, arc), pass `-z` or `--scanarchives` as an argument.  

To force Siegfried to pause for 1 second between file scans, pass `-t` or `--throttle` as an argument. 

To force Siegfried to log verbose output to the terminal while processing, pass `-v` or `--verbosesf` as an argument.

In Brunnhilde 1.9+, you can pass Brunnhilde a Siegfried CSV file via piped stdin with the `--stdin` flag or by providing the path to a Siegfried CSV file with `--csv CSV`. The `--stdin` and `--csv CSV` options are limited to directory sources and do not work with disk images. When using these options, make sure that the `source` argument passed to Brunnhilde matches the directory scanned by Siegfried. Otherwise some options (e.g. virus scanning, running bulk_extractor) and statistics (e.g. total size) will not work as expected.

### Specifying hash type  

Brunnhilde uses the md5 hash algorithm by default. Other options are sha1, sha256, sha512, or none.  

To change the type of hash used, pass `--hash HASH` as an argument to Brunnhilde, replacing HASH with your choice of sha1, sha256, or sha512.

If the user specifies not to calculate checksums with `--hash none`, the resulting CSV outputs and HTML report will not contain information calculated from hash values, namely information about duplicate files in the source.

### Report completeness  

In order to to keep the HTML from being excessively large, Brunnhilde does not include Siegfried warnings in the HTML report by default (the CSV is still created).  

To include Siegfried warnings in the report, pass `-w` or `--showwarnings` as an argument.

### bulk_extractor  

To enable scanning of files with bulk_extractor, pass `-b` or `--bulkextractor` as arguments. This is disabled by default. Results are written to a 'bulk_extractor' sub-directory. In addition, running bulk_extractor adds a Social Security Number (SSN) section to the HTML report.

In Brunnhilde 1.9+, it is possible to instruct bulk_extractor to search for user-supplied patterns. Use the `--regex` flag to supply the path a file containing newline-separated regular expressions: `--regex /path/to/regex_file.txt`.

Specify the ssn_mode passed to bulk_extractor with `--ssn_mode INT`. Valid choices are 0, 1, or 2. If not specified, Brunnhilde will default to 1. See the following explanation of the modes from the [bulkextractor 1.5 release notes](https://github.com/simsong/bulk_extractor/blob/master/doc/announce/announce_1.5.md):

```
SSN recognition: you are now able to specify one of three SSN recognition modes:  

-S ssn_mode=0 SSN’s must be labeled “SSN:”. Dashes or no dashes are okay.  
-S ssn_mode=1 No “SSN” required, but dashes are required.  
-S ssn_mode=2 No dashes required. Allow any 9-digit number that matches SSN allocation range.  
```

### Using disk images as input  

In `-d` mode, Brunnhilde uses SleuthKit's tsk_recover to export files from a disk image into a "carved files" directory for analysis. This works with raw images by default. In BitCurator or any other environment where libewf has been compiled into SleuthKit, Brunnhilde's -d mode also supports forensic disk image formats, including aff and ewf (E01). Due to the limitations of SleuthKit, Brunnhilde does not yet support characterizing disks that use the UDF filesystem.  

**Note: tsk_recover does not retain file system dates, so the date reporting functionality of Brunnhilde is limited for non-HFS disk images. It is advised to create DFXML or similar files to retain/analyze file system metadata such as date stamps. In Brunnhilde 1.6.0+, a fiwalk-generated DFXML file is created for all non-HFS disk images.**

By default, Brunnhilde will keep a copy of the files exported from disk images in a "carved_files" directory. If you do not wish to keep a copy of these files after reporting is finished, you can pass the `-r` or `--removefiles` flags as arguments to Brunnhilde, which will cause it to delete the "carved_files" directory once all other tasks have finished.

Brunnhilde also includes some options for more granular control of tsk_recover:

`-a`: Export only allocated files (by default, Brunnhilde passes the -e option to tsk_recover, instructing it to extract all files from disk images, including deleted files, for reporting)  
`--tsk_fstype`: Specify file system type in image (if not specified, tsk_recover will make best guess; to see possible values, type `tsk_recover -f list` in a terminal)  
`--tsk_imgtype`: Specify disk image type (if not specified, tsk_recover will make best guess; to see possible values, type `tsk_recover -i list` in a terminal)  
`--tsk_sector_offset`: Specify which volume on a disk to extract files from based on sector offset (see tsk_recover man page for more details)  

An example command for these values might be:  
`brunnhilde.py -d --tsk_fstype fat --tsk_imgtype ewf --tsk_sector_offset 59 sampleimage.E01 . test`

Disk image mode is not supported in Windows.

### HFS-formatted disk images  

*There is a known bug in older versions of unhfs, the command-line version of HFSExplorer, that prevented some files from being extracted from HFS disks. Be sure that you have the [bugfix release](https://sourceforge.net/projects/catacombae/files/HFSExplorer/0.23.1%20%28snapshot%202016-09-02%29/) of HFSExplorer installed. Versions of BitCurator since 1.7.106 are fine.*

To characterize HFS formatted disks in Brunnhilde, pass both the `-d` and `--hfs` flags as arguments, and be sure to use a raw disk image as the source (HFSExplorer is unable to process forensically packaged disk images). This functionality works "off the shelf" in BitCurator. Non-BitCurator environments will require you to install additional [dependencies](https://github.com/tw4l/brunnhilde#dependencies).  

To extract AppleDouble resource forks from HFS-formatted disk images, pass the `--hfs_resforks` or `--resforks` flag in addition to `-d` and `--hfs`.

To instruct `unhfs`/HFS Explorer to extract files from a speciic partition rather than using its default autodetection, pass the partition number as an integer with the `--hfs_partition` flag, e.g. `--hfs_partition 1`.

To instruct `unhfs`/HFS Explorer to extract only a specific file or directory from the HFS file system, pass the POSIX path with the `hfs_fsroot` flag, e.g. `--hfs_fsroot /Users/tessa/backup/` or `--hfs_fsroot "my backup.dmg"`.

### Dependencies

All dependencies are already installed in BitCurator 1.7.106+. See instructions below for installing dependencies if you wish to use Brunnhilde in a different environment (Linux, Mac, or Windows).

#### Internet connection (Brunnhilde 1.8 and below only)

In Brunnhilde 1.9+, an internet connection is no longer required.

Brunnhilde 1.8 and below requires an internet connection to download the HTML report's Bootstrap JavaScript and CSS dependencies. If you are using Brunnhilde 1.8 or below in an environment without an internet connection, you can manually copy the `assets` directory from the Brunnhilde source repo into a directory named `brunnhilde` in your user's home directory, or use the `--load_assets PATH` flag to specify an alternate path to a Brunnhilde `assets` directory to use.

In Brunnhilde 1.9, the HTML report no longer uses Bootstrap and so does not need to download or cache JavaScript and CSS files.

#### Core requirements (all operating systems)  

For Brunnhilde to report on any directory of content, the following must be installed in addition to Brunnhilde:

* Python (2.7 or 3.4+; Python 3 is recommended)
* [Siegfried](http://www.itforarchivists.com/siegfried): Brunnhilde is now compatible with all version of Siegfried, including 1.6+. It does not support MIME-Info or FDD signatures: for Brunnhilde to work, Siegfried must be using the PRONOM signature file only. If you have been using MIME-Info or FDD signatures as a replacement for or alongside PRONOM with Siegfried 1.5/1.6 on your machine, entering `roy build -multi 0` in the terminal should return you to Siegfried's default PRONOM-only identification mode and allow Brunnhilde to work properly.  
* [requests Python module](https://pypi.org/project/requests/): For downloading CSS and JS files for HTML report from this repository. This should be automatically installed as a dependency when Brunnhilde is installed via pip.

#### Additional dependencies (for full functionality in Linux and macOS)

Functions such as reporting on the contents of disk images, scanning for personally identifiable information (PII), and virus scanning introduce additional dependencies.

* [SleuthKit](http://www.sleuthkit.org/): Carves files from and creates DFXML reports for disk images containing FAT, NTSF, HFS+, EXT2/3, ISO9660, UFS, RAW, SWAP, and YAFFS2 file systems. Note: SleuthKit works only with raw disk images by default, and has additional dependencies such as [libewf](https://github.com/libyal/libewf) and [afflib](https://github.com/sshock/AFFLIBv3) that may or may not be installed depending on installation method for working with forensically-packaged disk images.  
* [HFSExplorer](http://www.catacombae.org/hfsexplorer/): Carves files from disk images containing HFS file system  
* [bulk_extractor](https://github.com/simsong/bulk_extractor): Scans for PII  
* [ClamAV](https://www.clamav.net): Scans for viruses  
* [tree](https://linux.die.net/man/1/tree): Reports on directory structure

#### Linux  

*Note: Assumes Debian-based distro. If other, use appropriate package manager or build from source.*  

* HFSExplorer: Download bin files from [bugfix snapshot](https://sourceforge.net/projects/catacombae/files/HFSExplorer/0.23.1%20%28snapshot%202016-09-02%29/) and move to /usr/share/hfsexplorer.  
* bulk_extractor: Build from source distribution using instructions found [here](https://github.com/simsong/bulk_extractor).  
* Other dependencies:  
```
# sleuthkit 
git clone git://github.com/sleuthkit/sleuthkit.git
cd sleuthkit
./bootstrap
./configure
make
sudo make install
sudo ldconfig

# clamav
sudo apt-get install clamav
sudo freshclam

# tree
sudo apt-get install tree
```  

#### macOS

*Note: If not already installed on your system, first install [Homebrew](https://brew.sh/).*

* HFSExplorer: Download bin files from [bugfix snapshot](https://sourceforge.net/projects/catacombae/files/HFSExplorer/0.23.1%20%28snapshot%202016-09-02%29/), unzip, rename directory to 'hfsexplorer' and move to /usr/local/share.  
* Other dependencies:  
```
brew install sleuthkit
brew install bulk_extractor
brew install clamav
brew install tree
```

#### Windows

*Note: Windows support for Brunnhilde is limited. Normal reporting of directories should work without issue. Scanning of disk images, virus scanning, generating tree reports, and running bulk_extractor are not currently supported in Windows.*

### Creators

* Canadian Centre for Architecture
* Tessa Walsh

This project was initially developed in 2016-2017 for the [Canadian Centre for Architecture](https://www.cca.qc.ca) by Tessa Walsh, Digital Archivist, as part of the development of the Archaeology of the Digital project.

### Thanks

Thank you to Richard Lehane for writing Siegfried, Ross Spencer for ideas and help, Kevin Powell for suggesting the additions of ClamAV and bulk_extractor and writing the initial code to integrate these tools, Brian Dietz for suggesting improvements in tsk_recover and macOS functionality, and to the PRONOM team at the UK National Archives for building and maintaining such a wonderful tool.  
