from os.path import join as j


project_dir = "/home/mot"
data_dir = j(project_dir, "data")
experiment_dir = j(data_dir, "experiments")
training_dir = j(data_dir, "training")
model_dir = j(project_dir, "py", "lib", "models")

detection_threshold = 75

CPUs = 16
GPUs = 4

crop_size = 64

use_magic_pixel_segmentation = True

ms_metric_cal = 13.94736842
ms_rescale = 1 / 4
