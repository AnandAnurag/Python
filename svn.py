import os
import subprocess
import re
import shutil
import sys
import getopt

from tqdm import tqdm

def getEnvironment(key):
    ENV_DICT = {'p' : 'v_01', 's': 'stage_02', 'c' : 'Prod Clone', 't': 'test_02'}
    if key in ['p', 'c', 's', 't']:
        return ENV_DICT[key]
    else:
        print('Environment not found! Valid choices are \'p\', \'c\', \'s\', \'t\' for Production, Cert, Stage and Test respectively.')
        exit()
    
def main(argv):
    ENV = None
    REV = None
    opts = getopt.getopt(argv, "hr:o:e:")[0]
    REPO = 'https://svn.cozeva.com:18080/svn/zh_svn'
    DEST = 'C:/Users/aanand/workspace/deployment'
    
    FILE_PATTERN = re.compile(r"(\/arwmodules\/.*\/)(.*\.(.*))")
    DIR_PATTERN = re.compile(r"(\/arwmodules\/.*\/)([^\.]+)")
    for opt, arg in opts:
        if(opt == '-h'):
            print('python svn.py -r <REV> -e <ENVIORNMENT:p|c|s|t>-o <OUTPUT_DIRECTORY>')
            return
        elif(opt == '-r'):
            REV = int(arg)
        elif(opt == '-e'):
            ENV = getEnvironment(arg)
        elif(opt == '-o'):
            DEST = arg
            if not os.path.isdir(DEST):
                os.mkdir(DEST)
    if REV is None:
        REV = int(input("Revison Number:"))
    if ENV is None:
        ENV = getEnvironment(input("Environment:"))

    output = subprocess.run(f"svn log {REPO} -r {REV} -v", shell=True,
                            stdout=subprocess.PIPE, text=True).stdout.splitlines()
    split_idx = output.index('')

    RM = re.search(r"#(\d+)",
                   output[split_idx+1], re.IGNORECASE).group(1)
    DEST = f"{DEST}/RM{RM}_{REV}".replace(' ', '%20')
    conf = set()
    clear_cache = False
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.mkdir(DEST)
    logs = output[3:split_idx]
    env_specific_logs = filter(lambda x: re.search(ENV, x), logs)
    for log in tqdm(env_specific_logs, desc="Preparing…", ascii=False, ncols=75):
        log = log.strip()
        action = log[0]
        filepath = log[2:].replace(' ', '%20')
        if action in ['M', 'A']:
            search = FILE_PATTERN.search(filepath)
            if search:
                export = f"svn export {REPO}{filepath}/@{REV} {DEST} --force"
                subprocess.run(export, shell=True,
                               stdout=subprocess.PIPE, text=True)
                extension = search.group(3)
                if extension in ['module', 'js', 'css']:
                    clear_cache = True
                conf.update(
                    [f"UI:{search.group(2)}:{extension}:cp|/sites/all/modules{search.group(1)}|1|:#0"])
            else:
                search = DIR_PATTERN.search(filepath)
                if search:
                    conf.update(
                        [f"UI:{search.group(2)}:dir:cpdir|/sites/all/modules{search.group(1)}|1|:#0"])
        elif action in ['D']:
            search = FILE_PATTERN.search(filepath)
            if search:
                conf.update(
                    [f"UI:{search.group(2)}:{extension}:rem|/sites/all/modules{search.group(1)}|1|:#0"])
            else:
                search = DIR_PATTERN.search(filepath)
                if search:
                    conf.update(
                        [f"UI:{search.group(2)}:dir:rmdir|/sites/all/modules{search.group(0)}|1|:#0"])
    if(len(conf) > 0):
        f = open(f"{DEST}/file.conf", "w")
        delimeter = "\n"
        f.write(delimeter.join(conf) +
                ("\nUI:css-js:sh:cc:#0" if clear_cache else ''))
        f.close()
        print(f"Deployment folder created at {DEST}")
    else:
        print(f"File not found!\nMake sure environment is correct from your below commit log:\n\n" + "\n".join(output))


if __name__ == "__main__":
    main(sys.argv[1:])
