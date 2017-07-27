# Create the normalized video
python ../Normalizer.py /local/scratch/mot/data/videos/validation/val1.avi /local/scratch/mot/data/backgrounds/validation/val1_background.png /local/scratch/mot/data/videos/validation/val1_normalized.avi
# Create the binary video
python ../BinaryExtractor.py /local/scratch/mot/data/videos/validation/val1_normalized.avi /local/scratch/mot/data/videos/validation/val1_binarized.avi -t 215 -inv
# Remove old demo databags
if [ -f /local/scratch/mot/data/bags/validation/val1_detectionExample.db ]; then
    rm /local/scratch/mot/data/bags/validation/val1_detectionExample.db
fi
# Create the database and store detection results
python ../ComponentExtractor.py /local/scratch/mot/data/videos/validation/val1_binarized.avi /local/scratch/mot/data/videos/validation/val1_normalized.avi /local/scratch/mot/data/bags/validation/val1_detectionExample.db