from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask import current_app as app
from flask import session
import urllib.request
import os
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import cv2
import numpy as np

computer_path = "C:/senier project/myapp/app/static/data/"

main = Blueprint('main', __name__, url_prefix='/')

@main.route('/', methods=['GET'])
def index():
    return render_template('/main/index.html')


@main.route('/crawl', methods=['POST'])
def crawl_images_route():
    global num_images
    global foldername
    global width
    global height
    keyword = request.form['keyword']
    foldername = request.form['folder_name']
    num_images = int(request.form['num_images'])
    width = int(request.form['width'])
    height = int(request.form['height'])

    crawl_images(keyword, foldername, num_images, width, height)
    return redirect('/results')


def crawl_images(keyword, foldername, num_images, width, height):
    search_name = keyword
    max_count = int(num_images) + 1
    folder_name = foldername

    service = Service()
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(service=service, options=options)
    driver.get("https://www.google.co.kr/imghp?hl=ko&tab=wi&authuser=0&ogbl")
    elem = driver.find_element(By.NAME, "q")
    elem.send_keys(search_name)
    elem.send_keys(Keys.RETURN)

    SCROLL_PAUSE_TIME = 1

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
    # 맨 아래로 스크롤하기
        if max_count < 50:
            break
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # 페이지 로딩 대기
        time.sleep(SCROLL_PAUSE_TIME)
    # 페이지가 로딩 된 후 새로운 페이지의 최대 스크롤 길이를 계산
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                driver.find_element(By.CSS_SELECTOR, ".LZ4I").click()
            except:
                break  
        last_height = new_height
    global save_path
    global aug_path
    global resize_path

    save_path = computer_path + folder_name + "/"  
    aug_path = computer_path + folder_name + "/_augmentationed/"
    resize_path = computer_path + folder_name + "/_aug_resized/"

    if not os.path.isdir(save_path): # 폴더가 존재하지 않는다면 폴더 생성
         os.makedirs(save_path)
    if not os.path.isdir(aug_path):
         os.makedirs(aug_path)
    if not os.path.isdir(resize_path):
         os.makedirs(resize_path)

    images = driver.find_elements(By.CSS_SELECTOR, ".rg_i.Q4LuWd")
    count = 1
    for image in images:
        try:
            image.click()
            time.sleep(2)
            imgUrl = driver.find_element(By.CSS_SELECTOR, '.sFlh5c.pT0Scc.iPVvYb').get_attribute("src")
            print(imgUrl)
            save_file = str(count) + ".jpg"
            urllib.request.urlretrieve(imgUrl, save_path + save_file)
            print("img file save success")
            count = count + 1
            if max_count == count:
                break
        except:
            if max_count == count:
                break
            pass
    
    
    driver.close()
    pass



def resize_images(folder_path, output_folder, width, height):
    # Ensure the folder path ends with a slash
    folder_path = folder_path.rstrip("/") + "/"

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # List all files in the folder
    files = os.listdir(folder_path)

    for file in files:
        # Check if the file is an image
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            # Open the original image
            with Image.open(folder_path + file) as img:
                # Resize the image with high-quality resampling (LANCZOS)
                resized_img = img.resize((width, height), Image.LANCZOS)
                # Save the resized image to the output folder
                resized_img.save(output_folder + file)


def tilt_image(img, tilt_angle):
    # Calculate the center of the original image
    center_x, center_y = img.width / 2, img.height / 2

    # Rotate the image around its center
    rotated_img = img.rotate(tilt_angle, resample=Image.BICUBIC, center=(center_x, center_y), fillcolor=(255, 255, 255))

    # Calculate the cropping box
    w, h = rotated_img.size
    left = (w - img.width) // 2
    top = (h - img.height) // 2
    right = (w + img.width) // 2
    bottom = (h + img.height) // 2

    # Crop the image
    cropped_img = rotated_img.crop((left, top, right, bottom))

    return cropped_img

def flip_image_lr(img):
    return img.transpose(Image.FLIP_LEFT_RIGHT)

def augment_images(folder_path, output_folder):
    # Ensure the folder path ends with a slash
    folder_path = folder_path.rstrip("/") + "/"

    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # List all files in the folder
    files = os.listdir(folder_path)

    for file in files:
        # Check if the file is an image
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):

                # Open the original image
            with Image.open(folder_path + file) as original_img:
                original_img = original_img.convert('RGB')
                    # Tilt the image (you can adjust the tilt angle as needed)
                tilted5_img = tilt_image(original_img, tilt_angle=5)
                tilted10_img = tilt_image(original_img, tilt_angle=10)
                tilted15_img = tilt_image(original_img, tilt_angle=15)
                    # Flip the image left/right
                flipped_lr_img = flip_image_lr(original_img)
                flipped_tilted5_lr_img = flip_image_lr(tilted5_img)
                flipped_tilted10_lr_img = flip_image_lr(tilted10_img)
                flipped_tilted15_lr_img = flip_image_lr(tilted15_img)

                # Save augmented images to the output folder
                original_img.save(output_folder + file.replace(".", "_original."))
                tilted5_img.save(output_folder + file.replace(".", "_tilted5."))
                tilted10_img.save(output_folder + file.replace(".", "_tilted10."))
                tilted15_img.save(output_folder + file.replace(".", "_tilted15."))
                flipped_lr_img.save(output_folder + file.replace(".", "_flipped_lr."))
                flipped_tilted5_lr_img.save(output_folder + file.replace(".", "_flipped_tilted5_lr."))
                flipped_tilted10_lr_img.save(output_folder + file.replace(".", "_flipped_tilted10_lr."))
                flipped_tilted15_lr_img.save(output_folder + file.replace(".", "_flipped_tilted15_lr."))

                print(f"Augmented {file} and saved to {output_folder}")


@main.route('/results', methods=['GET','POST'])
def results_page():

    image_file_names = ['data/' + foldername + '/' + str(x+1) + '.jpg' for x in range(num_images)]

    return render_template('/main/results.html', image_files=image_file_names, num_iamges = num_images, enumerate = enumerate)

@main.route('/end', methods=['GET','POST'])
def end_page():
    del_img =  request.form.getlist('del_img')
    print(del_img)
    for file in del_img:
        file_name = file + '.jpg'
        os.remove(save_path + file_name)
    augment_images(save_path, aug_path)
    print("img file augmentation success")
    resize_images(aug_path, resize_path, width, height)
    print("img file resize success")

    return render_template('/main/end.html')