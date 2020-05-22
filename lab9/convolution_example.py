import numpy as np
import scipy.signal as signal
from numpy.fft import fft2, ifft2
import matplotlib.pyplot as plt
import PIL.Image
import PIL.ImageDraw
from PIL.ImageOps import invert
from skimage.feature import peak_local_max
import itertools

# phases = [[cmath.phase(x) for x in dftimg[i]] for i in range(len(dftimg))]
# phases = phases/np.max(np.array(phases))*255
# imageio.imwrite("phases.jpg", np.array(255 - phases))
# absvals = np.abs(dftimg)
# absvals = absvals/np.max(np.array(absvals))*255

# imageio.imwrite("abs.jpg", np.array(255 - absvals))

def convulate(im, pattern):
    return np.real(ifft2(fft2(im) * fft2(np.rot90(pattern, 2), (im.shape[0], im.shape[1]))))

def print_dots(in_img_file, in_pattern_file, out_file, threshold=0.9, channels="rgb", inv = True):
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

    img_r = convulate(img_r, pattern_r)
    img_g = convulate(img_g, pattern_g)
    img_b = convulate(img_b, pattern_b)

    rgbs = np.zeros(np.shape(img_r))
    if 'r' in channels:
        rgbs += img_r
    if 'g' in channels:
        rgbs += img_g
    if 'b' in channels:
        rgbs += img_b

    convulation_lows = rgbs < threshold * np.max(rgbs)
    rgbs[convulation_lows] = 0
    found_max_coords = peak_local_max(rgbs)

    original_img = PIL.Image.open(in_img_file)
    draw = PIL.ImageDraw.Draw(original_img)

    pattern_width = pattern_arr.shape[1]
    pattern_height = pattern_arr.shape[0]
    
    for vec in found_max_coords:
        draw.rectangle([(vec[1], vec[0]), (vec[1] - pattern_width, vec[0] - pattern_height)], outline="red")
        draw.rectangle([(vec[1]+1, vec[0]+1), (vec[1] - pattern_width-1, vec[0] - pattern_height-1)], outline="red")

    original_img.save(out_file)

print_dots("img/galia.png", "img/galia_e.png", "res.png")
print_dots("img/school.jpg", "img/fish1.png", "res_rybki.png", inv=False, channels='r', threshold=0.25)