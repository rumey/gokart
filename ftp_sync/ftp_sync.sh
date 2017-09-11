#!/bin/bash

source ./utils.sh
source ./options.sh

info "Begin to synchronization."

sync_options="-P ${options["parallel"]}"
if [[ ${options["only-existing"]} -eq 1 ]]; then
    #only-existing mode is enabled
    sync_options="$sync_options --only-existing"
    if [[ ! -a "${options["sync-list-file"]}" ]]; then
        #sync list file does not exist, initialize one
        #retrieve all file names from remote-folder folder
        info "File '${options["sync-list-file"]}' does not exist, populate a default one"
        cmd=""
        if [[ "$options["remote-dir"]" == "" ]]; then
            cmd="open -u ${options["user"]},${options["password"]} ${options["ftp-url"]} && find " > "${options["sync-list-file"]}"
        else
            cmd="open -u ${options["user"]},${options["password"]} ${options["ftp-url"]} && cd ${options["remote-dir"]} && find " > "${options["sync-list-file"]}"
        fi
        tmp_file="/tmp/ftp_sync_$$_$(($(date +'%s * 1000 + %-N / 1000000')))"
        lftp -c "${cmd} > ${tmp_file}"
        return_code=$?;
        if [[ $return_code -ne 0 ]]; then 
            rm -f "${options["sync-list-file"]}"
            error "Failed to retrieve file list in remote folder '${options["remote-dir"]}' from ${options["ftp-url"]}"; 
            exit $return_code;
        fi
        for f in `sort ${tmp_file}`; do
            if [[ "$f" == "" ]]; then
                #empty file
                continue
            elif [[ "$f" =~ ^#.* ]]; then
                #comments
                continue
            elif [[ "$f" =~ /$ ]]; then
                #folders 
                continue
            elif [[ "$f" =~ ^\./ ]]; then
                f=${f#./}
            fi
            echo $f >> "${options["sync-list-file"]}"
        done
        rm -f "${tmp_file}"
        if [[ "${options["sync-list-filter"]}" != "" ]]; then
            source "${options["sync-list-filter"]}" "${options["sync-list-file"]}"
            return_code=$?; if [[ $return_code -ne 0 ]]; then exit $return_code; fi
        fi
    else
        info "File '${options["sync-list-file"]}' already exist."
    fi

    #read sync files from ${sync-list-file}
    index=-1
    while read -r f; do
	#trim spaces
        f="$(echo -e "${f}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
        #ignore the lines start with '#'
        if [[ ! ${f} = \#* ]]; then
            index=$(($index+1))
            files[$index]="${f}"
        fi
    done < "${options["sync-list-file"]}"
    files_length=$(($index + 1))

    if [[ files_length -eq 0 ]]; then
        error "No files are required to synchronize, please add the files into the file '${options["sync-list-file"]}' to synchronize or remove the file '${options["sync-list-file"]}' to let system populate the default sync list"
        exit 1
    fi

    #delete existing files if it is not included in file list from sync folder, because program only synchronize existing files
    for f in `ls ${options["sync-dir"]}`; do
        index=0
        found=0
        if [[ -d "${options["sync-dir"]}/${f}" ]]; then
            #is a directory
            continue
        fi
        while [[ ${found} -eq 0 ]] && [[ $index -lt ${files_length} ]]; do
            if [[ "${files[$index]}" == "${f}" ]]; then
                found=1
		break
            fi
            index=$(($index+1))
        done
        if [[ ${found} -eq 0 ]]; then
            #this file is not found in the .bom_files.txt file, no need to sync, delete it
            rm -f "${options["sync-dir"]}/${f}"
            debug "Disable synchronizing file '${f}' by deleting it from '${options["sync-dir"]}'"
        fi
    done

    #create dumy files in sync folder, because program only synchronize existing files
    for f in ${files[@]}; do
        if [[ ! -a "${options["sync-dir"]}/${f}" ]]; then
	    #create parent path if required
            parent_dir=`get_parent_path "${options["sync-dir"]}/${f}"`
            return_code=$?; if [[ $return_code -ne 0 ]]; then  error "$parent_dir"; exit $return_code; fi
	    create_dir "${parent_dir}"
            return_code=$?; if [[ $return_code -ne 0 ]]; then  error "$parent_dir"; exit $return_code; fi

            touch "${options["sync-dir"]}/${f}"
            debug "Enable synchronizing file '${f}' by creating a dumy file in '${options["sync-dir"]}'"
        fi
    done
fi
if [[ ${options["not-sync"]} -eq 1 ]]; then
    exit 0
fi

#start to synchronize the file between bom and local
info "${files_length} files will be synchronized from '${options["ftp-url"]}/${options["remote-dir"]}' to '${options["sync-dir"]}'"
#declare the try times if sync failed, and the waiting time before next try
waiting_times=(0 60 120 300 300)
return_code=1
for wait_time in ${waiting_times[@]}; do
    if [[ $wait_time -gt 0 ]]; then
        debug "Wait ${wait_time} seconds before try again."
        sleep $wait_time
    fi

    debug "Start to synchronize file from '${options["ftp-url"]}/${options["remote-dir"]}' to '${options["sync-dir"]}'"

    if [[ "$options["remote-dir"]" == "" ]]; then
        lftp -c "open -u ${options["user"]},${options["password"]} ${options["ftp-url"]} && lcd ${options["sync-dir"]} && mirror -c --recursion=always --no-perms --no-umask ${sync_options};" 
    else
        lftp -c "open -u ${options["user"]},${options["password"]} ${options["ftp-url"]} && cd ${options["remote-dir"]} && lcd ${options["sync-dir"]} && mirror -P 5 -c --recursion=always --no-perms --no-umask ${sync_options};" 
    fi
    return_code=$?

    if [[ $return_code -eq 0 ]]; then
        debug "End to synchronize files from '${options["ftp-url"]}/${options["remote-dir"]}' to '${options["sync-dir"]}'"
        break
    else
        error "Failed to synchronize files from '${options["ftp-url"]}/${options["remote-dir"]}' to '${options["sync-dir"]}'."
    fi
done
if [[ $return_code -ne 0 ]]; then  error "Failed to synchronize files from '${options["ftp-url"]}/${options["remote-dir"]}' to '${options["sync-dir"]}',process exits."; exit $return_code; fi

#switch the workspace from data-dir to sync-dir
info "Swich the workspce to '${options["sync-dir"]}'"

if [[ -a "${options["local-dir"]}" ]]; then
    rm -f "${options["local-dir"]}"
    return_code=$?; if [[ $return_code -ne 0 ]]; then  error "Failed to remove symbolic link '${options["local-dir"]}'."; exit $return_code; fi
fi
ln -s "${options["sync-dir"]}" "${options["local-dir"]}"

return_code=$?; if [[ $return_code -ne 0 ]]; then  error "Failed to create symbolic link '${options["local-dir"]}' to '${options["sync-dir"]}'."; exit $return_code; fi

#start to synchronize the file between local and work dir
info "${files_length} files will be synchronized from '${options["sync-dir"]}' to '${options["data-dir"]}'"
waiting_times=(0 60 60 60 60)
return_code=1
for wait_time in ${waiting_times[@]}; do
    if [[ $wait_time -gt 0 ]]; then
        debug "Wait ${wait_time} seconds before try again."
        sleep $wait_time
    fi

    debug "Start to synchronize file from '${options["sync-dir"]}' to '${options["data-dir"]}'"

    lftp -c "local mirror --no-perms --no-umask --recursion=always ${options["sync-dir"]} ${options["data-dir"]}"
    return_code=$?

    if [[ $return_code -eq 0 ]]; then
        debug "End to synchronize file from '${options["sync-dir"]}' to '${options["data-dir"]}'"
        break
    else
        error "Failed to synchronize files from '${options["sync-dir"]}' to '${options["data-dir"]}'."
    fi
done
if [[ $return_code -ne 0 ]]; then error "Failed to synchronize files from '${options["sync-dir"]}' to '${options["data-dir"]}', process exits."; exit $return_code; fi

#switch the workspace from sync-dir to data-dir
info "Swich the workspce to '${options["data-dir"]}'"
if [[ -a "${options["local-dir"]}" ]]; then
    rm -f "${options["local-dir"]}"
    return_code=$?; if [[ $return_code -ne 0 ]]; then  error "Failed to remove symbolic link '${options["local-dir"]}'."; exit $return_code; fi
fi
ln -s "${options["data-dir"]}" "${options["local-dir"]}"
return_code=$?; if [[ $return_code -ne 0 ]]; then  error "Failed to create symbolic link '${options["local-dir"]}' to '${options["data-dir"]}'."; exit $return_code; fi

info "`date` : End to synchronization"
info ""

