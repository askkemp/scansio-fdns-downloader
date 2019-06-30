## Introduction
Using rapid7 API download FDNS studies from Rapid7 scans.io. 

First gets a list of all files available at the FDNS study. Checks the filename against already downloaded files. For each file that needs to be downloaded, it generates a download link and proceeds to download the file using wget via subprocess. Wget is used to allow for easy download throttling (change `--limit-rate` in script). After file is downloaded, sha1 hash is collected and verified against API data. If the hash does not match, it appends '.ERROR' to filename.

## Logging
* Everything logged to file `logging.log`

## Requirements
* Rapid7 API key. Place into `rapid7APIKEY`
* Python2.7


## API Documentation
* https://opendata.rapid7.com/apihelp


## License
* agpl-3.0
