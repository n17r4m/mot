from util.DataBag import DataBag
from util.models.ClassyVCoderX import ClassyVCoder
from util.models.DeepVelocity_trainer_cropX import DV_trainer


bag = DataBag('/local/scratch/mot/data/bags/deepVelocity/tmp4.db')
CC = ClassyVCoder()
CC.load('/local/scratch/mot/util/models/ClassyVCoderX.96.h5')

trainer = DV_trainer(bag, CC)
trainer.fetch_data()
trainer.train(5)