import os
import string
import datetime
import pytz
import socket
import json
import platform
import subprocess

base_path = os.path.abspath(os.path.dirname(__file__))

def generate_app_profile():
    profile_template_file = os.path.join(base_path,"src/apps/profile-template.js")
    package_json_file = os.path.join(base_path,"package.json")

    with open(package_json_file) as f:
        package = json.loads(f.read())

    with open(profile_template_file) as f:
        profile_template = string.Template(f.read())

    app_name = package["config"]["app"]
    profile_name = os.path.join(base_path,"src/apps","{}-profile.js".format(app_name))

    now = datetime.datetime.now(pytz.timezone('Australia/Perth'))

    package.update(package['config'])
    package.update({
        "build_datetime":now.strftime("%Y-%m-%d %H:%M:%S %Z(%z)"),
        "build_date":now.strftime("%Y-%m-%d %Z(%z)"),
        "build_time":now.strftime("%H-%M-%S %Z(%z)"),
        "build_platform":platform.system(),
        "build_host":socket.gethostname()
    })

    #get the latest git commit.
    latest_commit = subprocess.check_output(["git","log","-n","1"]).splitlines()
    commit_info = {}
    for line in latest_commit:
        for k,v in [("commit","commit"),("Author:","commit_author"),("Merge:",""),("Date:","commit_date"),("","commit_message")]:
            if line[:len(k)] == k:
                if v and line[len(k):].strip() :
                    if v in commit_info:
                        commit_info[v] =  "{}\\n{}".format(commit_info[v],line[len(k):].strip())
                    else:
                        commit_info[v] = line[len(k):].strip()
                break

    package.update(commit_info)

    #get the branch info
    branch = [b for b in subprocess.check_output(["git","branch"]).splitlines() if b.strip().startswith("*")][0].strip()[1:].strip()
    
    #if branch.startswith("(detached from"):
    #    branch = branch[len("(detached from"):len(branch) - 1].strip()

    package["repository_branch"]=branch




    #tranform value to json string
    for k,v in package.iteritems():
        package[k] = json.dumps(v)

    profile = profile_template.safe_substitute(package)
    with open(profile_name,'wb') as f:
        f.write(profile)

if __name__ == "__main__":
    generate_app_profile()


