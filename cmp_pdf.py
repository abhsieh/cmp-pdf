import tkinter as tk
from TkinterDnD2 import *
from tkinter import ttk, font
import tkinter.filedialog as filedialog
from pdf2image import convert_from_path
from PIL import Image
from os import listdir
import sys, os
import cv2
from skimage.metrics import structural_similarity as compare_ssim
import imutils, shutil
from tkinter import messagebox
import argparse
import numpy as np
import json

poppler_path = r"bin"
first_tmp = "first_tmp"
sec_tmp = "sec_tmp"
result_tmp = "result_tmp"
pre_name = "tmp_"
result_name = 'result.pdf'
conf_file = "my_conf.json"
my_page = 0

def pdf_page2image(path, image_prename):
    #img = convert_from_path(path, 200, poppler_path=poppler_path, first_page=11, last_page=12)
    img = convert_from_path(path, 120, poppler_path=poppler_path)
    #print(path, "-->", img)
    for idx,page in enumerate(img):
        page.save(image_prename+str(idx).zfill(2)+'.jpg', 'JPEG')
    return 0
          
def image_diff(org_img, dest_img, result_img):
    # load the two input images
    imageA = cv2.imread(org_img)
    imageB = cv2.imread(dest_img)
    max_w, max_h = None, None
    if imageA.shape[:2] != imageB.shape[:2]:
        max_w = max(imageA.shape[0], imageB.shape[0])
        max_h = max(imageA.shape[1], imageB.shape[1])

    # convert the images to grayscale
    if max_w or max_h:
        grayA = cv2.cvtColor(
            imutils.resize(imageA, width=max_w, height=max_h), cv2.COLOR_BGR2GRAY)
        grayB = cv2.cvtColor(
            imutils.resize(imageB, width=max_w, height=max_h), cv2.COLOR_BGR2GRAY)
        if grayA.shape != grayB.shape:
            gray_max_w = max(grayA.shape[0], grayB.shape[0])
            gray_max_h = max(grayA.shape[1], grayB.shape[1])
            right_a, bottom_a = gray_max_h-grayA.shape[1],  gray_max_w-grayA.shape[0]
            right_b, bottom_b = gray_max_h-grayB.shape[1],  gray_max_w-grayB.shape[0]
            if (bottom_a, right_a) != (0, 0):
                grayA = cv2.copyMakeBorder(
                    grayA, 0, bottom_a, 0, right_a,
                    cv2.BORDER_CONSTANT, value=(0, 0, 0))
            if (bottom_b, right_b) != (0, 0):
                o_grayB = grayB.copy()
                grayB = cv2.copyMakeBorder(
                    grayB, 0, bottom_b, 0, right_b,
                    cv2.BORDER_CONSTANT, value=(0, 0, 0))
    else:
        grayA = filter_data(gray2binary(cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)))
        grayB = filter_data(gray2binary(cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)))

    # compute the Structural Similarity Index (SSIM) between the two
    # images, ensuring that the difference image is returned
    (score, diff) = compare_ssim(grayA, grayB, full=True, gaussian_weights = True)  # AB
    global my_page
    print("score= ", score, "page =", my_page)
    my_page += 1       
    diff = (diff * 255).astype("uint8")
    #print("SSIM: {}".format(score))

    # threshold the difference image, followed by finding contours to
    # obtain the regions of the two input images that differ
    #thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]   #AB
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV)[1]   #AB
    #AB-- cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    #AB-- cnts = imutils.grab_contours(cnts)
    contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # AB++
    cv2.drawContours(imageB, contours, -1, (0, 0, 255), 1) #AB++
    # loop over the contours
    #AB -- for c in cnts:
    #AB --     # compute the bounding box of the contour and then draw the
    #AB --     # bounding box on both input images to represent where the two
    #AB --     # images differ
    #AB --     (x, y, w, h) = cv2.boundingRect(c)
    #AB --     cv2.rectangle(imageA, (x, y), (x + w, y + h), (0, 0, 255), 2)
    #AB --    cv2.rectangle(imageB, (x, y), (x + w, y + h), (0, 0, 255), 2)
    cv2.imwrite(filename=result_img, img=imageB)
    
def gray2binary(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)[1]
    
def filter_box(image):
    tmp = cv2.boxFilter(image, -1, (10, 10), normalize = 1)
    tmp[tmp < 240] = 0
    return tmp
    
def filter_data(image):
    # 3*3核的高斯濾波
    gray = cv2.GaussianBlur(image, (5, 5), 0)
    # canny邊緣檢測
    gray = cv2.Canny(gray, 250, 255)
    return gray
    
def image2pdf(image_dir, pdf_path_name):
    image_list = []
    files = listdir(image_dir)
    files = sorted(files)
    for file in files:
        file = image_dir+"\\"+file
        img = Image.open(file)
        im = img.convert('RGB')
        image_list.append(im)
        #print(file)
    image_list[0].save(pdf_path_name, save_all =True, append_images = image_list[1:])

def get_path(num):
    if num == 0:
        file = filedialog.askopenfilenames(title = "Select file",filetypes = (("pdf files","*.pdf"),("all files","*.*")))
    elif num == 1:
        files = filedialog.askopenfilenames(title = "Select file",filetypes = (("excel files","*.xlsx"),("all files","*.*")))
    elif num == 2:
        file = filedialog.askdirectory(title = "Select Dir")
    #dest_dir, filename = os.path.split(files[0])
    
    file_str.set(file)

def deal_path(path_str):
    result = path_str
    if path_str[0] == "{":
        result = path_str[1:-1]
    return result    
    
def drop(event, text_name, num):
        text_name.set(deal_path(event.data))
        if num == 1:
            result = event.data
            result, filename = os.path.split(deal_path(result))
            result_str.set(result)
    
def cmp_file(first_path, sec_path, first_tmp, sec_tmp, result_tmp, result_filename):
#   first_path --> the first pdf file abs path
#   sec_path --> the secondary pdf file abs path
#   first_tmp --> the first pdf temp dir that pdf convert to image
#   sec_tmp --> the secondart pdf temp dir that pdf convert to image
#   result_tmp --> the final differeces image dir. 
#   result_filename --> the asb path that final pdf put.

    first_tmp_file = first_tmp + "/" + pre_name
    pdf_page2image(first_path, first_tmp_file)
    sec_tmp_file = sec_tmp + "/" + pre_name
    pdf_page2image(sec_path, sec_tmp_file)
    first_files = listdir(first_tmp)
    sec_files = listdir(sec_tmp)
    i = 0
    for first_file, sec_file in zip(first_files, sec_files):
        #print("org = ", org_file, "dest = ", dest_file)
        first_file = first_tmp + "/" + first_file
        sec_file = sec_tmp + "/" + sec_file
        result_file = result_tmp + "/" + str(i).zfill(2)+".jpg"
        #print("first -->", first_file)
        #print("sec -->", sec_file)
        #print("result -->", result_file)
        image_diff(first_file, sec_file, result_file)
        i += 1
    #print("result_filename = ", result_filename)
    image2pdf(result_tmp, result_filename)
    kill_tmp(first_tmp, sec_tmp, result_tmp)
    
def create_tmp(path, dir_name):
    dir_str, file_str = os.path.split(path)
    dir_str = dir_str + "/" + dir_name
    re_create(dir_str)
    return [path, dir_str]

def re_create(dir_str):
    if os.path.exists(dir_str):
        shutil.rmtree(dir_str, ignore_errors=True)
    os.mkdir(dir_str)
    
def kill_tmp(first_tmp = None, sec_tmp = None, result_tmp = None):
    kill_list = [first_tmp, sec_tmp, result_tmp]
    for tmp in kill_list:
        if tmp != None:
            if os.path.exists(tmp):
                shutil.rmtree(tmp, ignore_errors=True)
                
#AB++
def save_path(first, second, result):
    data = {'first':'', 'second':'', 'result':''}
    f = open(conf_file, "wt")
    data["first"] = first
    data["second"] = second
    data["result"] = result
    json.dump(data, f)
    f.close()
 
def gui_pre_cmp():
    first_path = first_str.get()
    first_list = create_tmp(first_path, first_tmp)
    #print(first_list)
    sec_path = sec_str.get()
    sec_list = create_tmp(sec_path, sec_tmp)
    #print(sec_list)
    result_path = result_str.get()
    save_path(first_path, sec_path, result_path)            # AB++
    result_filename = result_path + '/' + result_name
    result_path = result_path + '/' + result_tmp
    re_create(result_path)
    cmp_file(first_list[0], sec_list[0], first_list[1], sec_list[1], result_path, result_filename)
    messagebox.showinfo("The difference pdf file on below \n", result_filename)
    
def cli_pre_cmp():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--first", required=True, help="first pdf file")
    ap.add_argument("-s", "--second", required=True, help="second pdf file")
    args = vars(ap.parse_args())
    print("current dir =", os.getcwd())
    print("-f -->", args["first"])
    print("-s -->", args["second"])
    current_dir = os.getcwd()
    first_path = current_dir + "/" + args["first"]
    first_list = create_tmp(first_path, first_tmp)
    sec_path = current_dir + "/" + args["second"]
    sec_list = create_tmp(sec_path, sec_tmp)
    result_path = current_dir + result_tmp
    re_create(result_path)
    result_filename =  current_dir + '/' + result_name
    cmp_file(first_list[0], sec_list[0], first_list[1], sec_list[1], result_path, result_filename)
    print("The difference pdf file put on below path --> \n", result_filename)
    
def go_away():
    root.quit()
    root.destroy()
    sys.exit() 

def gui_intf(root):
    global first_str, sec_str, result_str
    conf_flag = False
    #root = TkinterDnD.Tk()
    w = 650
    h = 150
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))
    root.title("pdf comparison tool")
    #AB++++
    if os.path.isfile(conf_file):
        f = open(conf_file, "rt")
        my_path = json.load(f)
        f.close()
        conf_flag = True
    #+++++++++++++++++++++++++
    my_font_size = font.Font(size = 14)
# ----------- first pdf file box ----------------------------------
    first_str = tk.StringVar() # used to get path from input window
    first_file =tk.Entry(root, textvariable = first_str)
    first_str.set("drop the first file to here")
    if conf_flag: first_str.set(my_path["first"])    # AB++
    first_file['font'] = my_font_size
    first_file.drop_target_register(DND_FILES)
    first_file.dnd_bind('<<Drop>>', lambda event: drop(event, first_str, 0))
    first_file.grid(row = 0, column = 0, ipadx = 220, columnspan = 20, padx = 10, pady = 2, sticky = 'W')
# ---------- secondary pdf file box ---------------------------------
    sec_str = tk.StringVar() # used to get path from input window
    sec_file =tk.Entry(root, textvariable = sec_str)
    sec_str.set("drop the secondary file to here")
    if conf_flag: sec_str.set(my_path["second"])    # AB+++
    sec_file['font'] = my_font_size
    sec_file.drop_target_register(DND_FILES)
    sec_file.dnd_bind('<<Drop>>', lambda event: drop(event, sec_str, 1))
    sec_file.grid(row = 1, column = 0, ipadx = 220, columnspan = 20, padx = 10, pady = 2, sticky = 'W')
    
#---------------- result directory -----------------------------
    result_str = tk.StringVar() # used to get path from input window
    result_file =tk.Entry(root, textvariable = result_str)
    result_str.set("Result directory .....")
    if conf_flag: result_str.set(my_path["result"])    # AB+++
    result_file['font'] = my_font_size
    #result_file.drop_target_register(DND_FILES)
    #result_file.dnd_bind('<<Drop>>', lambda event: drop(event, result_str))
    result_file.grid(row = 2, column = 0, ipadx = 220, columnspan = 20, padx = 10, pady = 2, sticky = 'W')
 
    b_cmp = tk.Button(root, text = 'Compare', command = gui_pre_cmp, height = 1, width = 8)
    b_cmp['font'] = my_font_size
    b_cmp.grid(row=4, column=8, pady = 2)
    
    b_exit = tk.Button(root, text = 'Exit', command = go_away, height = 1, width = 5)
    b_exit['font'] = my_font_size
    b_exit.grid(row=4, column=11, pady = 2)
    root.mainloop()
	
if __name__ == '__main__':
    root = 0
    if len(sys.argv) > 1:       ### cli interface
        cli_pre_cmp()
    else:                       ### GUI interface
        root = TkinterDnD.Tk()
        #root.iconbitmap('logo_1.ico')
        gui_intf(root)
        
        
 # pyinstaller -F --add-data d:\tools\python_385\tcl\tkdnd2.8;tkdnd --path="d:\tools\python_385\lib\site-packages\cv2\cv2.cp38-win_amd64.pyd" -i "logo.ico" cmp_pdf.py
 # get cv2 file, print(cv2.__file__)