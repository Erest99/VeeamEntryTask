import filecmp
import logging
import os
import shutil
import sys
import time
import tkinter
from datetime import datetime
from difflib import Differ
from tkinter import filedialog

import constants


def syncFolders(differ, log_path):
    src_files = [constants.LOG_FILE]
    for src_p, src_f in absoluteFilePaths(source_path):
        src_files.append(src_f)
        rep_p = src_p.replace(source_path, replica_path)
        # check if file with same name exists in replica
        if os.path.exists(rep_p):
            # file exists in replica, check if it is updated
            if not filecmp.cmp(src_p, rep_p):
                with open(log_path, 'a') as f:
                    f.write(str(datetime.now()) + " ->\tUpdated file: " + rep_p + "\n")
                    # if not rewrite it
                    if rep_p.endswith(tuple(constants.SUPPORTED_TYPES)):
                        with open(src_p) as f1, open(rep_p) as f2:
                            line_num = 1
                            # minor formating bug
                            for line in differ.compare(f2.readlines(), f1.readlines()):
                                if line.startswith("+ ") or line.startswith("- "):  # not ideal
                                    f.write("\t[" + str(line_num) + "]:" + line)
                                    line_num += 1
                            f.write("\n")
                logging.info("File updated: " + rep_p)
                shutil.copy(src_p, rep_p)
        else:
            # if the file doesn't exist in replica then create it
            logging.info("Added file: " + rep_p)
            with open(log_path, 'a') as f:
                f.write(str(datetime.now()) + " ->\tAdded file: " + rep_p + "\n")
            os.makedirs(os.path.dirname(rep_p), exist_ok=True)
            shutil.copy(src_p, rep_p)
    # remove aditional files
    for rep_p, rep_f in absoluteFilePaths(replica_path):
        if not rep_f in src_files:
            logging.info("Removed file: " + rep_p)
            with open(log_path, 'a') as f:
                f.write(str(datetime.now()) + " ->\tRemoved file: " + rep_p + "\n")
            os.remove(rep_p)
        else:
            src_files.remove(rep_f)
    # remove empty folders
    deleteEmptyDirectory(replica_path)


def absoluteFilePaths(directory):
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f)), f


def deleteEmptyDirectory(root_path):
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=False):
        for d in dirnames:
            path = os.path.join(dirpath, d)
            if not os.listdir(path):
                os.rmdir(path)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # for debug
    root = tkinter.Tk()
    root.withdraw()
    print("Select source folder.")
    source_path = filedialog.askdirectory().replace("/", "\\")
    logging.info("Selected " + source_path + " as source")
    print("Select folder to replicate to.")
    replica_path = filedialog.askdirectory().replace("/", "\\")
    logging.info("Selected " + replica_path + " as replica")
    log_path = replica_path + "\\" + constants.LOG_FILE
    if not os.path.exists(source_path):
        # path error
        print("Path is no longer valid.")
        logging.exception("Folder " + source_path + " was moved, renamed or deleted, terminating")
        time.sleep(constants.TERMINATION_DELAY)
        sys.exit()
    if source_path in replica_path or replica_path in source_path:
        print("Selected folder can not be subdirectories.")
        logging.exception(
            "Selected folders are subdirectories: " + replica_path + " : " + source_path + " -> terminating")
        time.sleep(constants.TERMINATION_DELAY)
        sys.exit()
    # all ok
    differ = Differ()
    if len(os.listdir(replica_path)) > 0:
        print("Selected replica folder is not empty, all files will be deleted. Do you wish to continue? (Y/N)")
        logging.info("Selected replicating folder is not empty")
        if input() == "Y":
            print("Deleting all files.")
            logging.info("Deleting all files in " + replica_path + ".")
            shutil.rmtree(replica_path)
            os.mkdir(replica_path)
        else:
            print("Aborting synchronization.")
            logging.info("Run aborted.")
            time.sleep(constants.TERMINATION_DELAY)
            sys.exit()
    with open(log_path, 'w') as f:
        f.write(
            "This file contains logs for changes at: " + source_path + "\n\nSynchronization started at: " + str(
                datetime.now()) + "\n")
    print("Synchronization started.")
    logging.info("Synchro started with src: " + source_path + " and rep: " + replica_path)
    while True:
        for src_p, src_f in absoluteFilePaths(source_path):
            if constants.LOG_FILE in src_f:
                logging.warning(
                    "Source folder can't contain file named '" + constants.LOG_FILE + "'. Do you wish to remove it? (Y/N)")
                if input() == "Y":
                    os.remove(src_p)
                else:
                    print("Terminating.")
                    logging.info("Terminating, logging file name collision.")
                    time.sleep(constants.TERMINATION_DELAY)
                    sys.exit()
        time.sleep(constants.SYNC_PERIOD)
        print("Updating")
        logging.info("Updating repository at: " + replica_path)
        syncFolders(differ, log_path)
