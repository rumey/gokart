#!/bin/bash

echo "Begin to synchronization at `date`"

server="ftp://ftp.bom.gov.au/"
user="bom771"
password="B5o5GlNt"
sync_dir="adfd"

#get the local dir of bom data
root_dir=$1
if [[ -z "$root_dir" ]] 
then
    root_dir="/var/www/bom_data"
fi

local_work_dir="$root_dir/$sync_dir"
local_sync_dir="$root_dir/$sync_dir/.cache"
#create the local dir if required
for d in "$root_dir" "$local_work_dir" "$local_sync_dir"; do
    if [[ ! -a "$d" ]]; then
        mkdir "$d"
    elif [[ ! -d "$d" ]]; then
        echo "$d is not directory."
        exit 1
    fi
done

bom_files="$root_dir/.bom_files"
#prepare bom files need to be synchronized
if [[ -a "$bom_files" ]] && [[ ! -f "$bom_files" ]]; then
    #.bom_files.txt is not a regular file
    echo "$bom_files is not a regular file"
fi

declare -a files=()
files_length=0
if [[ ! -a "$bom_files" ]]; then
    #.bom_files.txt does not exist, initialize one
    #retrieve all file names from bom/adfd folder
    echo "File '$bom_files' does not exist, populate a default one"
    lftp -c "open -u $user,$password $server && cd $sync_dir && cls -B; close" > /tmp/bom_files
    file_name=""
    file_ext=""
    previous_file_name=""
    previous_file_ext=""
    index=-1
    for f in `sort /tmp/bom_files`; do
        file_name=$f
        #get the file name and ext
        while [ $file_name != ${file_name%.*} ]; do
            file_name="${file_name%.*}"
        done
        #get the file ext
        file_ext=${f#$file_name.*}
        if [[ "$previous_file_name" != "$file_name" ]]; then
            #new file, add to the file list
            index=$(($index+1))
            files[$index]="$f"
            previous_file_name=$file_name
            previous_file_ext=$file_ext
        elif [[ $file_ext == "grb" ]]; then
            #current file is a grb file, a prefered format
            files[$index]="$f"
            previous_file_ext=$file_ext
        fi
    done
    files_length=$(($index + 1))
    echo "$files_length files are populated and will be synchronized from $server/$sync_dir to $local_sync_dir"
    #write the bom files into file .bom_files.txt
    for f in `sort /tmp/bom_files`; do
        index=0
        found=0
        while [[ $found -eq 0 ]] && [[ $index -lt $files_length ]]; do
            if [[ "${files[$index]}" == "$f" ]]; then
                found=1
            fi
            index=$(($index+1))
        done
        if [[ $found -eq 0 ]]; then
            #no need to synchronize
            echo "#$f" >> $bom_files
        else
            #need to synchronize
            echo $f >> $bom_files
        fi
    done
    #remove temp file
    rm /tmp/bom_files
else
    index=-1
    for f in `cat $bom_files`; do
        f="$(echo -e "${f}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        #ignore the lines start with '#'
        if [[ ! $f = \#* ]]; then
            index=$(($index+1))
            files[$index]="$f"
        fi
    done
    files_length=$(($index + 1))
fi

if [[ files_length -eq 0 ]]; then
    echo "No files are required to synchronize, please add the files which need to be synchronized into the file '$bom_files'"
    exit 1
fi

#delete existing files if it is not included in file list from sync folder, because program only synchronize existing files
for f in `ls $local_sync_dir`; do
    index=0
    found=0
    while [[ $found -eq 0 ]] && [[ $index -lt $files_length ]]; do
        if [[ "${files[$index]}" == "$f" ]]; then
            found=1
        fi
        index=$(($index+1))
    done
    if [[ $found -eq 0 ]]; then
        #this file is not found in the .bom_files.txt file, no need to sync, delete it
        rm "$local_sync_dir/$f"
        echo "Disable synchronizing file $local_sync_dir/$f by deleting it from '$local_sync_dir'"
    fi
done

#create dumy files in sync folder, because program only synchronize existing files
for f in ${files[@]}; do
    if [[ ! -a "$local_sync_dir/$f" ]]; then
        touch "$local_sync_dir/$f"
        echo "Enable synchronizing file $local_sync_dir/$f by creating a dumy file in '$local_sync_dir'"
    fi
done

#start to synchronize the file between bom and local
echo "$files_length files will be synchronized from '$server$sync_dir' to '$local_sync_dir'"
lftp -c "open -u $user,$password $server && cd $sync_dir && lcd $local_sync_dir && mirror -P 5 -c --only-existing; close" 

#start to synchronize the file between local and work dir
echo "$files_length files will be synchronized from '$local_sync_dir' to '$local_work_dir'"
lftp -c "local mirror -r $local_sync_dir $local_work_dir"
echo "End to synchronization at `date`"
echo "========================================================================================================"

