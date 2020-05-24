import numpy as np
from numpy.fft import fft2, ifft2
import matplotlib.pyplot as plt
import PIL.Image
import PIL.ImageDraw
from PIL.ImageOps import invert
from skimage.feature import peak_local_max
import cv2

def convolute(im, pattern, plotting=False):
    img_dft = fft2(im)
    if plotting:
        plt.imshow(np.abs(img_dft))
        plt.show()
        plt.imshow(np.angle(img_dft))
        plt.show()
    pattern_dft = fft2(np.rot90(pattern, 2), im.shape)

    return np.real(ifft2(img_dft * pattern_dft))

def find_pattern(in_img_file, in_pattern_file, out_file=None, threshold=0.9, channels="rgb", inv = True, outline="red", plotting=False):
    img = PIL.Image.open(in_img_file).convert("RGB")

    if inv:
        img = invert(img)
    
    img_arr = np.asarray(img)
    img_r, img_g, img_b = img_arr[:,:,0], img_arr[:,:,1], img_arr[:,:,2]

    pattern = PIL.Image.open(in_pattern_file).convert("RGB")

    if inv:
        pattern = invert(pattern)
    
    pattern_arr = np.asarray(pattern)
    pattern_r, pattern_g, pattern_b = pattern_arr[:,:,0], pattern_arr[:,:,1], pattern_arr[:,:,2]

    conv_sum = np.zeros(img_r.shape)

    if 'r' in channels:
        if plotting:
            print("Red channel DFT abs and phase")
        conv_sum += convolute(img_r/255, pattern_r/255, plotting)
    if 'g' in channels:
        if plotting:
            print("Green channel DFT abs and phase")
        conv_sum += convolute(img_g/255, pattern_g/255, plotting)
    if 'b' in channels:
        if plotting:
            print("Blue channel DFT abs and phase")
        conv_sum += convolute(img_b/255, pattern_b/255, plotting)

    if plotting:
        print("Convolutions sum")
        plt.imshow(conv_sum)
        plt.show()

    convolution_lows = conv_sum < threshold * np.max(conv_sum)
    conv_sum[convolution_lows] = 0
    found_max_coords = peak_local_max(conv_sum)

    original_img = PIL.Image.open(in_img_file)
    draw = PIL.ImageDraw.Draw(original_img)

    pattern_width = pattern_arr.shape[1]
    pattern_height = pattern_arr.shape[0]
    
    for vec in found_max_coords:
        draw.rectangle([(vec[1], vec[0]), (vec[1] - pattern_width, vec[0] - pattern_height)], outline=outline)
        draw.rectangle([(vec[1]+1, vec[0]+1), (vec[1] - pattern_width-1, vec[0] - pattern_height-1)], outline=outline)

    if out_file is not None:
        original_img.save(out_file)
    return len(found_max_coords), original_img