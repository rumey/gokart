#!/bin/bash

options["server"]="ftp.bom.gov.au"
options["user"]="bom771"
options["password"]="B5o5GlNt"
options["root-dir"]="/var/www/bom_data"
options["local-dir"]="adfd"
options["remote-dir"]="adfd"
options["only-existing"]=1
options["sync-list-filter"]="./bom_filter.sh"
options["parallel"]=5
