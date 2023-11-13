import sys
import os
import logging
import time
import shutil
import filecmp
from distutils.dir_util import copy_tree
# from tkinker.filedialog import askdirectory

import constants


def askLocation(instruction_string):
    print(instruction_string)
    attempt = 0
    while True:
        path = input()
        if os.path.exists(path):
            # valid path
            break
        else:
            attempt += 1
            if attempt >= constants.MAX_ATTEMPTS:
                # exceeded max number of attempts
                print("Exceeded maximum attempts, terminating")
                logging.info("Exceeded maximum attempts(" + str(constants.MAX_ATTEMPTS) + "), terminating")
                time.sleep(constants.TERMINATION_DELAY)
                sys.exit()
            else:
                # not exceeded max number of attempts
                print("Please enter valid path")
                logging.info("wrong attempt num " + str(attempt))

    return path


def syncFolders():
    src_files = []
    for src_p, src_f in absoluteFilePaths(source_path):
        src_files.append(src_f)
        rep_p = src_p.replace(source_path, replica_path)
        # check if file with same name exists in replica
        if os.path.exists(rep_p):
            # check if files are identical TODO edit
            if not filecmp.cmp(src_p, rep_p):
                # if not rewrite it
                logging.info("File rewrote: " + rep_p)
                shutil.copy(src_p, rep_p)

        else:
            # if the file doesn't exist in replica then create it
            logging.info("Added file: " + rep_p)
            os.umask(0)
            os.makedirs(os.path.dirname(rep_p), exist_ok=True)
            shutil.copy(src_p, rep_p)
    for rep_p, rep_f in absoluteFilePaths(replica_path):
        if not rep_f in src_files:
            os.remove(rep_p)


def absoluteFilePaths(directory):
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f)), f
        # for d in dirnames:
        #     yield os.path.abspath(os.path.join(dirpath, d)), d


if __name__ == '__main__':
    # TODO create option to browse folders
    # source_path = askLocation("Enter source folder path.")
    # replica_path = askLocation("Enter path to replica folder.")
    source_path = r"C:\Users\Horky\Desktop\source"
    replica_path = r"C:\Users\Horky\Desktop\replica"
    if source_path == replica_path:
        # identical paths of source and replica
        print("Source path and target replica path must be different, terminating.")
        logging.exception("Identical source and replica path: " + replica_path + " -> terminating")
        time.sleep(constants.TERMINATION_DELAY)
        sys.exit()
    if not os.path.exists(source_path):
        # path error
        print("Path is no longer valid.")
        logging.exception("Folder " + source_path + " was moved, renamed or deleted, terminating")
        time.sleep(constants.TERMINATION_DELAY)
        sys.exit()
    else:
        # all ok
        # TODO edit comparation of files to line by line -> so you can log what changed
        # TODO remake changes according to source - content of files, permissions
        # TODO log changes to file and logger
        if len(os.listdir(replica_path)) > 0:
            print("Selected replica folder is not empty, all files will be deleted. Do you wish to continue? (Y/N)")
            logging.info("Selected replicating folder is not empty")
            if input() == "Y":
                print("Deleting all files.")
                logging.info("Deleting all files in " + replica_path + ".")
                # for f in os.listdir(replica_path):
                #     os.remove(os.path.join(replica_path, f))
                shutil.rmtree(replica_path)
                os.mkdir(replica_path)
            else:
                print("Aborting synchronization.")
                logging.info("Run aborted.")
                time.sleep(constants.TERMINATION_DELAY)
                sys.exit()
        print("Synchronization started.")
        logging.info("Synchro started with src: " + source_path + " and rep: " + replica_path)
        while True:
            time.sleep(constants.SYNC_PERIOD)
            print("Updating")
            logging.info("Updating repository at: " + replica_path)
            syncFolders()
