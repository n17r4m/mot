#
#
# This code is not well maintained, mostly for reference if we revisit the
#  deep particle simulation/ related experiments.
#
#
import numpy as np
import cv2

from fauxtograph import VAE, GAN, VAEGAN, get_paths, image_resize
import matplotlib.pyplot as plt

%matplotlib tk

loader ={}
loader['enc'] = 'VAEGAN/new_arch_test_epoch20_enc.h5'
loader['dec'] = 'VAEGAN/new_arch_test_epoch20_dec.h5'
loader['disc'] = 'VAEGAN/new_arch_test_epoch20_disc.h5'
loader['enc_opt'] = 'VAEGAN/new_arch_test_epoch20_enc_opt.h5'
loader['dec_opt'] = 'VAEGAN/new_arch_test_epoch20_dec_opt.h5'
loader['disc_opt'] = 'VAEGAN/new_arch_test_epoch20_disc_opt.h5'
loader['meta'] = 'VAEGAN/new_arch_test_epoch20_meta.json'

vg2 = VAEGAN.load(flag_gpu=False, **loader)
shape = 3, vg2.latent_width

random_data = np.random.standard_normal(shape).astype('f')*3.
fake_images = vg2.inverse_transform(random_data, test=True)
reconstruct = vg2.inverse_transform(vg2.transform(fake_images))

# real_drop1 = cv2.imread('/Users/kevingordon/cims/drops/normalized_gray/d10-1.png')
# real_drop2 = cv2.imread('/Users/kevingordon/cims/drops/normalized_gray/d100-1.png')
# real_drop3 = cv2.imread('/Users/kevingordon/cims/drops/normalized_gray/d1000-1.png')

paths = get_paths('/Users/kevingordon/cims/drops/tmp_subset/')
real_images = vg2.load_images(paths)
real_recon1 = vg2.inverse_transform(vg2.transform(real_images))


plt.figure(figsize=(16,12))

for i in range(3):
    ax = plt.subplot(4, 10, i+1)
    plt.imshow(real_images[i].transpose(1,2,0))
    plt.axis("off")
    if i==4:
        ax.set_title("Randomly Sampled Real Images")
    ax = plt.subplot(4, 10, 10+i+1)
    plt.imshow(real_recon1[i])
    plt.axis("off")
    if i==4:
        ax.set_title("Reconstruction of Randomly Sampled Real Images")
    ax = plt.subplot(4, 10, 20+i+1)
    plt.imshow(fake_images[i])    
    plt.axis("off")
    if i==4:
        ax.set_title("Randomly Sampled Simulated Images")
    ax = plt.subplot(4, 10, 30+i+1)
    plt.imshow(reconstruct[i])    
    plt.axis("off")  
    if i==4:
        ax.set_title("Reconstruction of Randomly Sampled Simulated Images")
plt.show()