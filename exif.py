#pip install pywin32  
#import piexif
import os
import sys
import io
import glob
import time
import tempfile
#from PIL import Image
#import PIL
#from PIL import Image, ExifTags
#from PIL.ExifTags import TAGS
import subprocess
import base64
import argparse
import ctypes  # An included library with Python install.

delim='/safgfgdsg554h/'
file_name_code="%n$"

def Mbox(title, text, style):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)
    #cancel ==2
    #yes==6
    #no==7
                
def RunCommand(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    if process.returncode != int(0):
        print(cmd)
        for line in process.stdout:
            print(line)

def BulkEncode(file_path):
    files=[]
    
    #discover the relivent files
    exposure_path="\\Exposure Software"
    if os.path.exists(file_path+exposure_path):
        image_files=[]
        for file in glob.iglob(file_path+'\\*', recursive=False):
            # skip copies
            if "_original" in file:
                continue
            # skip folders
            if os.path.isfile(file):
                image_files.append(file)
            
        print("xmp_file")
        for xmp_file in glob.iglob(file_path+exposure_path+"\\**", recursive=True):
            # skip folders
            if not os.path.isfile(file):
                continue
            filename = os.path.basename(xmp_file)
            file_parts = filename.split(".")
            for im_f in image_files:
                if file_parts[0] in im_f:
                    common_prefix = os.path.commonprefix([xmp_file, im_f])
                    #print(common_prefix)
                    relitive_path = xmp_file.replace(common_prefix, "")
                    #print(relitive_path)
                    relitive_path = relitive_path.replace(file_parts[0], file_name_code)
                    
                    edit_time = os.path.getmtime(xmp_file)
                    notes = "app:exposure\n"
                    notes += "path:" + relitive_path + "\n"
                    edit = str(edit_time)
                    notes += 'edited:' + edit + '\n'
                    files.append((xmp_file, im_f, notes))
                    
    print("encoding")
    cmds = []
    for file in files:
        # xmp to image
        cmd = 'exiftool.exe -UserComment=\"'+file[2]+'\" -b -tagsfromfile \"'+file[0]+'\" -xmp '+file[1]
        print(cmd)
        cmds.append(cmd)
        #cmd = 'exiftool.exe -UserComment=\"'+file[2]+'\" -b '+file[1]

    for cmd in cmds:
        RunCommand(cmd)
        
    return
    #parpallel?

    
    
def Encode(file_path):
    app="Exposure"
    xmp_folder ='Exposure Software'
    filename=os.path.basename(file_path)
    parrent_dir=os.path.dirname(file_path)
    
    filename, file_extension = os.path.splitext(file_path)
    
    # bulk
    if len(file_extension) <= int(0):
        BulkEncode(file_path)
        return

    xmp_path=''
    #find xmp file
    for file in glob.iglob(xmp_folder+'\\**\\**', recursive=True):
        if filename in file:
            xmp_path = file

    print("xmp_path: "+xmp_path)

    if len(xmp_path) <= 0:
        print("ERROR: could not find xmp file")
        exit()

    edit_time = os.path.getmtime(xmp_path)
    if len(xmp_path) > 0:
        f = open(xmp_path, "r+b")
        xmp_data=f.read()
        f.close()

    #create temp file
    file_parts=filename.split('.')
    temp_file=''
    if len(parrent_dir)>0:
        temp_file = parrent_dir +"/" + file_parts[0]+'_temp.txt'
    else:
        temp_file = file_parts[0]+'_temp.txt'
    
    f = open(temp_file, "w")
    
    f.write("app"+delim+app+"\r\n")
    f.write("path"+delim+xmp_path+"\r\n")
    f.write("edit"+delim+str(edit_time)+"\r\n")
    f.write("data"+delim+str(base64.b64encode(xmp_data)))
    f.close()

    cmd ='exiftool.exe -overwrite_original -usercomment<='+temp_file+' '+file_path
    RunCommand(cmd)
    os.remove(temp_file)

def BulkDecode(file_path): 
    print("bulk decode")
    with tempfile.TemporaryDirectory() as temp_path:
        # extract xmp's
        cmd ='exiftool.exe -o \"'+temp_path+'\%f.xmp\" -xmp '+file_path    
        RunCommand(cmd)
            
        # extract notes
        cmd ='exiftool.exe -UserComment \"'+file_path+'\" -b ./ -w \"'+temp_path+'\%f.txt\"'
        RunCommand(cmd)
            
        txt_files=[]
        xmp_files=[]
        #match files and figure out what to do with them
        for file in glob.iglob(temp_path+'\**', recursive=False):
            filename, file_extension = os.path.splitext(file)
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
                    notes=f.readlines()
                    f.close()                   
                    # get data
                    path=app=edit=''
                    for line in notes:
                        lines = line.split(":")
                        if lines[0] == 'path':
                            path=lines[1].strip()
                        elif lines[0] == 'app':
                            app=lines[1].strip()
                        elif lines[0] == 'edited':
                            edit=lines[1].strip()
                                
                    if len(path) == 0:
                        print("Error, no path in "+ txt)
                        continue
                    
                    if not os.path.lexists(os.path.dirname(file_path+"\\"+path)):
                        os.makedirs(os.path.dirname(file_path+"\\"+path))

                    #move temp file to correct location
                    new_name= file_path+"\\"+path
                    new_name= new_name.replace(file_name_code, os.path.basename(txt_name))
                    time.sleep(1)
                     
                    if os.path.exists(new_name):
                        existing_edited = os.path.getmtime(new_name)
                        if existing_edited > float(edit):
                            file_name =  os.path.basename(new_name)
                            res = Mbox('OVEWRITE '+file_name, file_name +'\nxmp destination is newer do you want to overwrite?', 3)

                            if res == 6: # yes
                                os.replace(xmp, new_name)
                                time.sleep(1)
                                # set edit time
                                os.utime(new_name, (float(edit), float(edit)))
                            elif res == 6: # no
                                continue
                            elif res == 2: # cancel remaining
                                return
                    else:
                        if os.path.exists(new_name):
                            os.replace(xmp, new_name)
                        else:
                            os.rename(xmp, new_name)
                        time.sleep(1)
                        # set edit time
                        os.utime(new_name, (float(edit), float(edit)))                    

def Decode(file_path):
    filename=os.path.basename(file_path)
    parrent_dir=os.path.dirname(file_path)
    
    filename, file_extension = os.path.splitext(file_path)
    
    # bulk
    if len(file_extension) <= int(0):
        BulkDecode(file_path)
    return
        
    #exiftool -if "not $TAG" <RestOfCommand>    
    cmd ='exiftool.exe -usercomment '+file_path+' -w+ _temp.txt'
    RunCommand(cmd)

    temp= os.path.splitext(file_path)[0]+'_temp.txt'
    temp_data=''
    f = open(temp, "r")
    temp_data=f.read()
    f.close()
    os.remove(temp)

    trash= temp_data.find(":")+2
    temp_data= temp_data[trash:]
    
    #split on newlines 
    x = temp_data.split('...')
    path=''
    app=''
    edit=''
    data=''
    for line in x:
        lines = line.split(delim)
        if lines[0] == 'path':
            path=lines[1]
        elif lines[0] == 'app':
            app=lines[1]
        elif lines[0] == 'edit':
            edit=lines[1]
        elif lines[0] == 'data':
            data=lines[1]

    print("path: "+path)
    print("edit: "+edit)
    xmp=base64.b64decode(data[1:-1]).decode('UTF-8')

    if os.path.exists(path):
        edit_time = os.path.getmtime(path)
        if edit_time < float(edit):
            print("Cannot update")
            exit()
    else:
        dir = os.path.dirname(path)
        os.makedirs(dir)

    xmp.replace('\r','').replace('\n','')
    with open(path, 'w', encoding='UTF-8') as f:
        f.write(xmp)

    print("updated")
    

def Remove(file_path):
    #app="Exposure"
    #xmp_folder ='Exposure Software'
    #filename=os.path.basename(file_path)
    #parrent_dir=os.path.dirname(file_path)

    cmd ='exiftool.exe -overwrite_original -usercomment="" '+file_path
    RunCommand(cmd)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-e","--encode",action='store_true')
    parser.add_argument("-d","--decode",action='store_true')
    parser.add_argument("-r","--remove",action='store_true')
    parser.add_argument("-f", "--file", help="path to input file", type=str, required=True)

    # args are global
    args = parser.parse_args()
    print(args.encode)
    print(args.decode)
    
    if args.encode and not args.decode:
        Encode(args.file)
    elif args.decode and not args.encode:
        Decode(args.file)
    elif args.remove:
        Remove(args.file)
    else:
        print("Expects encode, decode, OR remove parameter")