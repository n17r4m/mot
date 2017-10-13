### Line scan to databag
from util.ComponentExtractor import ComponentExtractor
from util.DataBag import DataBag
from util.LinePipe import LinePipe

bag = DataBag('../../data/linescan/tmp_bag.db')
lp = LinePipe('/mnt/SIA/BU-2017-07-27/MSBOT-01039.bin')
extractor = ComponentExtractor(bag, lineScan=True)

binary = lp.binarize(150000, 200000, 130)
intensity = lp.normalized

extractor.extract(0, binary, intensity)

bag.commit()
