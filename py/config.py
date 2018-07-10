from os.path import join as j

tmp_dir = "/tmp/mot"
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
ms_rescale = 1 / 1
ms_detection_threshold = 0.75
ms_fps = 300.
ms_roi = ((950, 1450), (650, 1150))
