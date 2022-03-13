#!/usr/bin/python3
# Aplicaiton for emdeding and extracting xmp sidecar files from images
# Created by Mikeal Simburger (Simburger.com)
# Mar 13th 2021
# requires exiftool.exe
# tested in windows python 3.8.6

import os
import sys
import glob
import time
import tempfile
import subprocess
import argparse
import ctypes

delim = '/delim$*@/@*$delim/'
file_name_code = "%n$"
exif_path = 'exiftool.exe '
processes_count = os.cpu_count()


def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)


def RunParallelCommand(cmds):
    proc_list = []
    loop_num = len(cmds)
    for i in range(len(cmds)):
        process = subprocess.Popen(cmds[i],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        
        proc_list.append(process)
        if (i + 1) % processes_count == 0 or (i + 1) == loop_num:
            # max_Wait for the end of all processes for each process
            for subproc in proc_list:
                subproc.wait()
                # print error info
                if subproc.returncode != int(0):
                    print('')
                    print(cmds[i])
                    # only print if error
                    for line in subproc.stderr:
                        print(line)
                    for line in subproc.stdout:
                        print(line)
            proc_list = []
    return


def RunCommand(cmd):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    process.wait()
    if process.returncode != int(0):
        print(cmd)
        for line in process.stdout:
            if "Win32::API" in line.decode('ascii'):
                continue
            print(line.decode('ascii'))
        for line in process.stderr:
            if "Win32::API" in line.decode('ascii'):
                continue
            print(line.decode('ascii'))
    return


def Encode(file_path):
    files = []

    # discover the relivent files
    exposure_path = "\\Exposure Software"

    dir_path = file_path
    if os.path.isfile(dir_path):
        dir_path = os.path.dirname(dir_path)

    file_filter = ''
    if os.path.isfile(file_path):
        filename = os.path.basename(file_path)
        file_parts = filename.split(".")
        file_filter = file_parts[0]

    if os.path.exists(dir_path+exposure_path):
        image_files = []
        for file in glob.iglob(dir_path+'\\*', recursive=False):
            # skip copies
            if "_original" in file:
                continue
            # skip folders
            if os.path.isfile(file):
                image_files.append(file)

        for xmp_file in glob.iglob(dir_path+exposure_path+"\\**", recursive=True):
            # skip folders
            if not os.path.isfile(xmp_file):
                continue
            filename = os.path.basename(xmp_file)
            file_parts = filename.split(".")
            for im_f in image_files:
                # filter to desired file
                if len(file_filter) > 0:
                    if file_filter not in im_f:
                        continue

                if file_parts[0] in im_f:
                    common_prefix = os.path.commonprefix([xmp_file, im_f])
                    # print(common_prefix)
                    relitive_path = xmp_file.replace(common_prefix, "")
                    # print(relitive_path)
                    relitive_path = relitive_path.replace(file_parts[0], file_name_code)

                    edit_time = os.path.getmtime(xmp_file)
                    notes = "app:exposure\n"
                    notes += "path:" + relitive_path + "\n"
                    edit = str(edit_time)
                    notes += 'edited:' + edit + '\n'
                    files.append((xmp_file, im_f, notes))

    cmds = []
    for file in files:
        cmd = exif_path + '-m -UserComment=\"'+file[2]+'\"'+' -b -tagsfromfile\"'+file[0]+'\" -xmp \"'+file[1]+'\"'
        cmds.append(cmd)

    print("embeding xmp's")
    RunParallelCommand(cmds)
    return


def Decode(file_path):
    print("decode xmp data")
    with tempfile.TemporaryDirectory() as temp_path:
        # extract xmp's
        cmd = exif_path + ' -m -q -o \"'+temp_path+'\%f.xmp\" -xmp ' + file_path
        RunCommand(cmd)

        # extract notes
        cmd = exif_path + ' -m -q -UserComment \"'+file_path+'\" -b -w \"' + temp_path + '\%f.txt\"'
        RunCommand(cmd)

        txt_files = []
        xmp_files = []
        # match files and figure out what to do with them
        for file in glob.iglob(temp_path+'\**', recursive=False):
            file_extension = os.path.splitext(file)
            if ".txt" in file_extension:
                txt_files.append(file)
                continue
            if ".xmp" in file_extension:
                xmp_files.append(file)

        for txt in txt_files:
            txt_name, txt_ext = os.path.splitext(txt) 
            for xmp in xmp_files:
                if txt_name in xmp:
                    f = open(txt, "r")
                    notes = f.readlines()
                    f.close()
                    # get data
                    path = app = edit = ''
                    for line in notes:
                        lines = line.split(":")
                        if lines[0] == 'path':
                            path = lines[1].strip()
                        elif lines[0] == 'app':
                            app = lines[1].strip()
                        elif lines[0] == 'edited':
                            edit = lines[1].strip()

                    if len(path) == 0:
                        print("Error, no path in "+ txt)
                        continue

                    make_dir = file_path
                    if os.path.isfile(make_dir):
                        make_dir = os.path.dirname(make_dir)

                    if not os.path.lexists(os.path.dirname(make_dir+"\\"+path)):
                        os.makedirs(os.path.dirname(make_dir+"\\"+path))

                    # move temp file to correct location
                    new_name = make_dir+"\\"+path
                    new_name = new_name.replace(file_name_code, os.path.basename(txt_name))

                    time.sleep(1)

                    if os.path.exists(new_name):
                        existing_edited = os.path.getmtime(new_name)
                        if existing_edited > float(edit):
                            file_name = os.path.basename(new_name)
                            res = Mbox('OVEWRITE '+file_name, file_name +
                                       '\nxmp destination is newer do you want to overwrite?', 3)

                            if res == 6:  # yes
                                os.replace(xmp, new_name)
                                time.sleep(1)
                                # set edit time
                                os.utime(new_name, (float(edit), float(edit)))
                            elif res == 6:  # no
                                continue
                            elif res == 2:  # cancel remaining
                                return
                    else:
                        if os.path.exists(new_name):
                            os.replace(xmp, new_name)
                        else:
                            os.rename(xmp, new_name)
                        time.sleep(1)
                        # set edit time
                        os.utime(new_name, (float(edit), float(edit)))              
    return


def Remove(file_path):
    print("removing emded xmp data")
    res = Mbox('Removing xmp data?', 'Removing ALL emded xmp data from: ' +
               file_path, 1)

    if res == 1:  # yes
        cmd = exif_path + '-overwrite_original -usercomment = "" -xmp:all = "-all:all<xmp:time:all" '+file_path
        RunCommand(cmd)
        print("removed xmp data")
    elif res == 2:  # cancel
        print("cancelled")
        return -1
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Emdeds and extracts xmp sidecar files from images')

    parser.add_argument("-e", "--encode",
                        action='store_true',
                        help="embed xmp into image")

    parser.add_argument("-d", "--decode",
                        action='store_true',
                        help="extract xmp from image")

    parser.add_argument("-r", "--remove",
                        action='store_true',
                        help="delete xmp from image")

    parser.add_argument("-f", "--file",
                        help="single file or folder",
                        type=str, required=True)

    # print help message if bad input
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(0)

    res = ''
    start = time.time()
    if args.encode and not args.decode and not args.remove:
        Encode(args.file)
    elif args.decode and not args.encode and not args.remove:
        Decode(args.file)
    elif args.remove:
        res = Remove(args.file)
    else:
        print("Expects encode, decode, OR remove parameter")
        exit()

    # no durration if cancelled
    if res != -1:
        end = time.time()
        print("durration: %f sec" % (end-start))
