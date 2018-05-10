import os
import zipfile
import json


def zip_dir(dirname, zipfilename):
    filelist = []
    # Check input ...
    fulldirname = os.path.abspath(dirname)
    fullzipfilename = os.path.abspath(zipfilename)
    print("Start to zip {0} to {1}...".format(fulldirname, fullzipfilename))
    if not os.path.exists(fulldirname):
        print("Dir/File %s is not exist, Press any key to quit..." % fulldirname)
        inputStr = input()
        return
    if os.path.isdir(fullzipfilename):
        tmpbasename = os.path.basename(dirname)
        fullzipfilename = os.path.normpath(
            os.path.join(fullzipfilename, tmpbasename))
    if os.path.exists(fullzipfilename):
        print(
            "%s has already exist, are you sure to modify it ? [Y/N]" % fullzipfilename)
        while 1:
            # inputStr = input()
            inputStr = "Y"
            if inputStr == "N" or inputStr == "n":
                return
            else:
                if inputStr == "Y" or inputStr == "y":
                    print("Continue to zip files...")
                    break

    # Get file(s) to zip ...
    if os.path.isfile(dirname):
        filelist.append(dirname)
        dirname = os.path.dirname(dirname)
    else:
        # get all file in directory
        for root, dirlist, files in os.walk(dirname):
            for filename in files:
                filelist.append(os.path.join(root, filename))

    # Start to zip file ...
    destZip = zipfile.ZipFile(fullzipfilename, "w")
    for eachfile in filelist:
        destfile = eachfile[len(dirname):]
        print("Zip file {0}...".format(destfile))
        destZip.write(eachfile, destfile)
    destZip.close()
    print("Zip folder succeed!")


app_info = './data/app.json'
with open(app_info) as json_file:
    data = json.load(json_file)

appName = data["name"]
appVerson = data['version']
os.system("{}\pyinstaller_exe.bat".format(os.getcwd()))
dirname = "./dist/run/"
zipfilename = "{0}_v{1}_x64.zip".format(appName, appVerson)
zip_dir(dirname, zipfilename)
