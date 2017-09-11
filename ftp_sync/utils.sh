#!/bin/bash

#get the absolute path, 
#no exception
#$1: required. relative path or absolutive path, 
#$2: optinal. work path, default is `pwd`; if $1 is a relative path, it is a path under this path
get_absolute_path() {
    local path=$1
    local current_path=`pwd`
    if [[ $# -gt 1 ]] && [[ $2 != "" ]]; then
        current_path=`get_absolute_path $2`
    fi
    if [[ ! "$path" =~ ^/.* ]]; then
        if [[ "$path" =~ ^\./.* ]]; then
            path=`echo $path | sed -e 's/^\.\/\+//'`
        fi
        path="$current_path/$path"
    else
        path=`echo $path | sed -e 's/^\/\+/\//'`
    fi
    #remove tail /
    if [[ "$path" != "/" ]]; then
        path=`echo "$path" | sed -e 's/\/\+$//'`
    fi

    echo $path
}

#create dir
#has exceptions
#create parent dir if not exist
#failed if this dir or its parent dir exist and is not directory
#$1: the path to create; can be a absolute path or relaive path under `pwd`
create_dir() {
    local path=`get_absolute_path $1`
    if [[ ! -a $path ]]; then
        #not exist
        local declare new_dirs=("$path")
        local index=0
        local parent_path=$path
        #find all the folders need to be created
        while [[ $parent_path != "/" ]]; do
            parent_path=`echo $parent_path | sed -e 's/\/[^\/]\+$//'`
            if [[ $parent_path == "" ]]; then
                parent_path="/"
            fi
            if [[ ! -a $parent_path ]]; then
                #parent path does not exist
                index=$(($index+1))
                new_dirs[index]=$parent_path
            elif [[ ! -d $parent_path ]]; then
                #parent path exist but not a directory
                echo "$parent_path is not a directory"
                return 1
            else
                #parent path exist and is a directory
                break
            fi
        done
        #create the folders
        while [[ $index -ge 0 ]]; do
            mkdir ${new_dirs[$index]}
            return_code=$?; if [[ $return_code -ne 0 ]]; then  return $return_code; fi
            index=$(($index - 1))
        done
    elif [[ ! -d $path ]]; then
        #exist but not a directory
        echo "$path is not a directory"
        return 1
    fi
}

#get the parent dir
#has exceptions
#$1 path whose parent dir will be returned
get_parent_path() {
    local path=`get_absolute_path $1`
    if [[ $path == "/" ]]; then
        echo "Root path has no parent path"
        return 1
    fi
    parent_path=`echo $path | sed -e 's/\/[^\/]\+$//'`
    if [[ $parent_path == "" ]]; then
        parent_path="/"
    fi
    echo $parent_path
}

