# Using rapid7 API download FDNS studies from Rapid7 scans.io. Includes download throttling and sha1hash verification.
# Copyright (C) 2018 Kemp Langhorne
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import requests
import json
import os.path
from subprocess import Popen, PIPE # for sha1 hashing and wget
import logging


#
# Configuration
#
rapid7APIKEY = "YOUR-KEY-HERE"
logfilename="logging.log"


#
# Logging
#
logger = logging.getLogger('rapid7Downloder')
logger.setLevel(logging.INFO)
# create a file handler
handler = logging.FileHandler(logfilename)
handler.setLevel(logging.INFO)
# create a logging format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(handler)
logger.info('Starting Script')


def get_page(url):
     r = requests.get(url, headers={'X-Api-Key':rapid7APIKEY})
     responseDict = r.json() # dict
     return responseDict

def do_subprocess(cmd,fname):
    '''
    input: list, string
    '''
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    #print p.returncode
    if p.returncode > 0:
        logger.error("%s - exit status > 0 in subprocess. Command was: %s" % (fname,cmd))
        logger.error(stderr)
        os.rename(fname,fname + ".ERROR") # if download fails, move flie. If hash fails, move file.
        logger.error("Exiting on error!")
        exit()
    else:
        return stdout


#
# Download the list of files in the Forward DNS Study
#
# Documentation of API: https://opendata.rapid7.com/apihelp/
fDNSstudy = get_page("https://us.api.insight.rapid7.com/opendata/studies/sonar.fdns_v2/")
fDNSstudyFiles = fDNSstudy["sonarfile_set"]

# Process each file in study
for filename in fDNSstudyFiles:
    if os.path.isfile(filename): # Check if we have file
        logger.info("%s - Already have file" % filename)
    else: # Download missing file
        logger.info("%s - Need to download" % filename)

        # 
        # Capture metadata from study filename
        #
        logger.debug("%s - Capturing file metadata" % filename)
        FileMetadata = get_page("https://us.api.insight.rapid7.com/opendata/studies/sonar.fdns_v2/%s/" % filename )
        if "detail" in FileMetadata: # Bad: this key is normally not there # "Not found"
            logger.error("%s - error: %s" % (filename,FileMetadata))
            logger.error("Exiting on error!")
            exit()
        else:
            #print(FileMetadata) # {u'updated_at': u'2018-10-06', u'size': 16232380356, u'name': u'2018-10-05-1538741159-fdns_a.json.gz', u'fingerprint': u'560d9eb491f6dd347fc903f7665bfb773c04ad66'}
            FileMetadataSHA1 = FileMetadata["fingerprint"]

        #
        # Have to generate a download link based on study filename
        #
        logger.debug("%s - Generating download link" % filename)
        FindFileDownloadLink = get_page("https://us.api.insight.rapid7.com/opendata/studies/sonar.fdns_v2/%s/download/" % filename)
        if "detail" in FindFileDownloadLink: # Bad: this key is normally not there # "Request was throttled."
            logger.error("%s - Error generating download link. Script generated link: %s" % (filename,FindFileDownloadLink))
            logger.error("Exiting after error!")
            exit()
        if "url" in FindFileDownloadLink:    # Good
            IsFileDownloadLink = FindFileDownloadLink["url"]
            logger.info("%s - Downloading hash %s from %s" % (filename,FileMetadataSHA1,IsFileDownloadLink))

            #
            # Download file based on previously generated download link
            #
            wgetCmd = ['wget', '--limit-rate', '6m', '--output-document='+filename, IsFileDownloadLink]
            do_subprocess(wgetCmd,filename)


            #
            # Check SHA1 hash of download file against previously captured metadata
            #
            #logger.debug("    - Checking sha1 hash")
            fileSHA1Hash = do_subprocess(['sha1sum',filename],filename).split(" ")[0]
            logger.debug("%s - Online metadata says sha1shash is: %s" % (filename,FileMetadataSHA1))
            logger.debug("%s - Downloaded file sha1hsah is: %s" % (filename,fileSHA1Hash))
            if FileMetadataSHA1 == fileSHA1Hash:
                logger.info("%s - Hash of metadata matches hash of downloaded" % filename)
            else:
                logger.error("%s - HASH MISMATCH!" % filename)
                os.rename(filename,filename + ".ERROR") # if hash mismatch, rename file.
                #logger.error("Exiting on error!")
                #exit()


