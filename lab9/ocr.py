import numpy as np
import scipy.signal as signal
import cmath
from numpy.fft import fft2, ifft2
import cv2
import matplotlib.pyplot as plt
from skimage.feature import peak_local_max
import itertools
import pylcs

hamlet_text = """To be, or not to be, that is the question
Whether tis nobler in the mind to suffer
The slings and arrows of outrageous fortune,
Or to take arms against a sea of troubles
And by opposing end them. To die, to sleep,
No more and by a sleep to say we end
"""

def show_image(img):
    cv2.imshow("image", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def binarize(img):
    return cv2.threshold(img, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

def deskew(img):
    _0 ,_, angle = cv2.minAreaRect(np.argwhere(img > 100)[:,::-1])
    undo_rotation = -angle
    if undo_rotation > 45:
        undo_rotation -= 90
    (h, w) = img.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, -undo_rotation, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC)
    return rotated

def convolute(im, pattern):
    return np.real(ifft2(fft2(im) * fft2(np.rot90(pattern, 2), im.shape)))

available_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                     'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
available_digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
available_signs = [',', '.', '?', '!']

def load_font_files(font_name, letters=available_letters, digits=available_digits, signs=available_signs):
    character_files = {}
    for letter in letters:
        character_files[letter] = f'img/{font_name}/{letter}.png'

    for digit in digits:
        character_files[digit] = f'img/{font_name}/{digit}.png' 

    for sign in signs:
        character_files[sign] = f'img/{font_name}/s{sign}_.png'
    return character_files

def find_character(img, pattern, threshold=0.95):
    convolution = convolute(img/255, pattern/255)

    convolution_lows = convolution < threshold * max([np.max(convolution), 0.95*len(np.argwhere(pattern == 255))])

    convolution[convolution_lows] = 0
    found_max_coords = peak_local_max(convolution)

    return found_max_coords

def ocr(in_file, out_file, font_name="times", threshold=0.95):
    img = cv2.imread(in_file, cv2.IMREAD_GRAYSCALE)
    original_img = img.copy()

    character_files = load_font_files(font_name)

    translated_text = ""
    character_width = {}
    character_height = {}
    character_pattern = {}

    for character in character_files:
        pattern = cv2.bitwise_not(binarize(cv2.imread(character_files[character], cv2.IMREAD_GRAYSCALE)))
        character_pattern[character] = pattern
        character_width[character] = pattern.shape[1]
        character_height[character] = pattern.shape[0]

    characters_sorted = list(sorted(character_files, key=lambda ch: -len(np.argwhere(character_pattern[ch] == 255))))
    
    rotated = binarize(deskew(cv2.bitwise_not(img)))
    found_characters = np.zeros(rotated.shape, dtype = np.uint8)

    for character in characters_sorted:
        pattern = character_pattern[character]
        for coords in find_character(rotated, pattern, threshold):
            the_biggest = True 
            for y in range(coords[0] - character_height[character] + 2, coords[0]):
                for x in range(coords[1] - character_width[character] + 2, coords[1]):
                    if found_characters[y, x] != 0:
                        the_biggest = False
            if the_biggest:
                found_characters[coords[0]-character_height[character]+2:coords[0], coords[1]-character_width[character]+2:coords[1]] = ord(character)
    
    found_characters_cp = found_characters.copy()
    y = 0
    while y < found_characters.shape[0]:
        if all(found_characters[y,:] == 0):
            y += 1
            continue

        last_x = -1
        lowest_y = 0
        x = 0
        while x < found_characters.shape[1]:
            character = None
            for y_off in range(y - 10, y + 10):
                if 0 <= y_off and y_off < found_characters.shape[0]: 
                    ord_num = found_characters[y_off,x]
                    if ord_num != 0:
                        y = y_off
                        character = chr(ord_num)
                        break
            if character is not None:
                while found_characters[y-1, x] == ord(character):
                    y -= 1 
                while found_characters[y, x-1] == ord(character):
                    x -= 1
                x += character_width[character]
                y += character_height[character] 

                found_characters[y-character_height[character]:y, x-character_width[character]:x] = 0
                lowest_y = max([lowest_y, y])
                y -= character_height[character] // 2
                if x - last_x > character_width[character]*0.8:
                    if last_x != -1 and x - last_x > character_width[character] + 4:
                        translated_text += " "
                    translated_text += character
                last_x = x
            x += 1
        translated_text += "\n"
        y = lowest_y + 10

    return original_img, translated_text, found_characters_cp
