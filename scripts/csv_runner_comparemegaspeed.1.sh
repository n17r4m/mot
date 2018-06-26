# MEGASPEED COMMANDS
# ms1_dir=/home/mot/tmp/batchprocess_deblur/ #without blur
ms1_dir=/home/mot/tmp/batchprocess_deblur/ # Kevin's previous processing
ms2_dir=/home/mot/tmp/batchprocess_blur/ #with blur


python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010200000007_Tracking.txt" $ms1_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010200000007_Tracking.txt" "Glass Beads 150-180um video #20"
python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010290000016_Tracking.txt" $ms1_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010290000016_Tracking.txt" "Glass Beads 150-180um video #29"
python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010300000017_Tracking.txt" $ms1_dir"Glass.Bead.Tests/150.to.180.um/MSBOT-010300000017_Tracking.txt" "Glass Beads 150-180um video #30"

python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/200.to.300.um/MSBOT-010340000021_Tracking.txt" $ms1_dir"Glass.Bead.Tests/200.to.300.um/MSBOT-010340000021_Tracking.txt" "Glass Beads 200-300um video #34"

python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/212.to.250.um/MSBOT-010180000005_Tracking.txt" $ms1_dir"Glass.Bead.Tests/212.to.250.um/MSBOT-010180000005_Tracking.txt" "Glass Beads 212-250um video #18"
python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/212.to.250.um/MSBOT-010380000025_Tracking.txt" $ms1_dir"Glass.Bead.Tests/212.to.250.um/MSBOT-010380000025_Tracking.txt" "Glass Beads 212-250um video #38"

python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/300.to.335.um/MSBOT-010160000003_Tracking.txt"  $ms1_dir"Glass.Bead.Tests/300.to.335.um/MSBOT-010160000003_Tracking.txt" "Glass Beads 300-335um video #16"
python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/300.to.335.um/LineScan01036/detections.csv" $ms1_dir"Glass.Bead.Tests/300.to.335.um/MSBOT-010360000023_Tracking.txt" "Glass Beads 300-335um video #36"

python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/425.to500.um/MSBOT-010140000001_Tracking.txt" $ms1_dir"Glass.Bead.Tests/425.to500.um/MSBOT-010140000001_Tracking.txt" "Glass Beads 425-500um video #14"
python csv_proc_comparemegaspeed.1.py $ms2_dir"Glass.Bead.Tests/425.to500.um/MSBOT-010270000014_Tracking.txt" $ms1_dir"Glass.Bead.Tests/425.to500.um/MSBOT-010270000014_Tracking.txt" "Glass Beads 425-500um video #27"
