import sys
import re
import json
import getopt
import traceback
import mysql.connector

from zipfile import ZipFile
from tqdm import tqdm


def main(argv):
    ENV_DICT = {'p': 'prd', 's': 'stg', 'c': 'cert', 't': 'test'}
    WORKING_DIR = "{}\..\\".format(__file__)
    with open("{}\config.json".format(WORKING_DIR), 'r') as config:
        DB_CONFIG = json.load(config)['mysql']
    opts = getopt.getopt(argv, "e:")[0]
    for opt, arg in opts:
        if(opt == '-e'):
            if arg in ENV_DICT:
                DB_CONFIG['host'] = DB_CONFIG['host'].format(ENV_DICT[arg])
            else:
                exit("Invalid environment")
    try:
        print("Connecting {} ...".format(DB_CONFIG['host']))
        mydb = mysql.connector.connect(**DB_CONFIG)
        print("DB connected")
    except:
        exit('DB connection failed')

    try:
        mycursor = mydb.cursor()

        def getRoutineType(name):
            mycursor.execute(
                "SELECT r.`ROUTINE_TYPE` FROM `information_schema`.`ROUTINES` r WHERE r.`ROUTINE_NAME` = '{}'".format(name))
            res = mycursor.fetchall()
            return res[0][0]

        def getSourceCode(name):
            mycursor.execute("SHOW CREATE {} {}".format(
                getRoutineType(name), name))
            res = mycursor.fetchall()
            return res[0][2]
        with open("{}\..\input.txt".format(__file__), "r") as f:
            routineList = [re.sub(r"[^a-zA-Z_]", "", routine)
                           for routine in f.read().split("\n")]
        print(routineList)
        argsLen = len(routineList)
        DIR = "C:/Users/aanand/Downloads/sql_files"
        if argsLen > 1:
            with ZipFile("{}/sql.zip".format(DIR), "w") as zip:
                # Add multiple files to the zip
                for routine in tqdm(routineList, desc="Zipping...", ascii=False, ncols=75):
                    sourceCode = getSourceCode(routine)
                    zip.writestr("{}.sql".format(routine), sourceCode)
        elif argsLen == 1:
            routine = routineList[0]
            with open("{}/{}.sql".format(DIR, routine), "w") as f:
                sourceCode = getSourceCode(routine)
                f.write(sourceCode)
        else:
            exit("Routines list cannot be empty")
        print("Files prepared successfully")
    except:
        traceback.print_exception(*sys.exc_info())
    finally:
        mycursor.close()
        mydb.close()
        print("DB connection closed")


if __name__ == "__main__":
    main(sys.argv[1:])
