# MEGASPEED COMMANDS
ms_dir=/home/mot/tmp/batchprocess_deblur/ #without blur
ls_dir=/home/mot/tmp/batchprocess_blur/ #with blur

# invert velocities for glass bead test
python csv_proc_comparemegaspeed.py $ls_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010200000007_Tracking.txt" $ms_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010200000007_Tracking.txt" "Glass Beads 150-180um video #20"

python csv_proc_comparemegaspeed.py /home/mot/tmp/deconv_csv/MSBOT-010160000003A_VT_Tracking.txt /home/mot/data/exports/batchTest/Glass.Bead.Tests/300.to.335.um/MSBOT-010160000003_Tracking.txt 


python csv_proc_comparemegaspeed.py /home/mot/tmp/batchprocess_blur/MSBOT-010200000007_Tracking.txt /home/mot/tmp/batchprocess_deblur/MSBOT-010200000007_Tracking.txt
