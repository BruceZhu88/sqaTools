# -------------------------------------------------------------------------------
# Name:        Clear_folders
# Purpose:
#
# Author:      Bruce.Zhu
#
# Created:     14/09/2017
# Copyright:   (c) SQA 2017
# Licence:     <your licence>
# -------------------------------------------------------------------------------
import os
import shutil


def walk_folders(folder):
    folderscount = 0
    filescount = 0
    size = 0
    # walk(top,topdown=True,onerror=None)
    for root, dirs, files in os.walk(folder):
        folderscount += len(dirs)
        filescount += len(files)
        size += sum([os.path.getsize(os.path.join(root, name))
                     for name in files])
    return folderscount, filescount, size


def remove_file(path, fileType):
    if os.path.exists(path):
        folderscount, filescount, size = walk_folders(path)
        for parent, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if fileType in filename:
                    try:
                        delFilePath = os.path.join(parent, filename)
                        os.remove(delFilePath)
                    except Exception as e:
                        print(e)


def remove_folders(path, folderType):
    if os.path.exists(path):
        folderscount, filescount, size = walk_folders(path)
        for parent, dirnames, filenames in os.walk(path):
            if folderType in parent:
                # print(parent)
                try:
                    shutil.rmtree(parent)
                except Exception as e:
                    print(e)


def remove_folder(folder_path):
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)


# remove_file('./src', '.pyc')
remove_folders('./src', '__pycache__')
remove_folder('./__pycache__')
remove_folder('./log')
remove_folder('./dist')
remove_folder('./build')
