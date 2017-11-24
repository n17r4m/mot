#------------------------------------------------------------------------------#
#                                                                              #
#  A validation  example                                                       #
#  Will require the pymot and munkres libraries                                #
#  Note: pymot module should be modified as per KG for bug fix and point eval  #
#  In iPython: copy -> %paste the following in the interpreter                 #
#                                                                              #
#------------------------------------------------------------------------------#

from Bag2PymotJson import Bag2PymotJson
from pymot.pymot import MOTEvaluation
from DataBag import DataBag

gt = DataBag("../data/bags/deepVelocity/tmp8.db")
hyp = DataBag("../data/bags/deepVelocity/tmp8_tracking.db")

gt_converter = Bag2PymotJson(gt, ground_truth=True)
hyp_converter = Bag2PymotJson(hyp, ground_truth=False)

json_tracking_data1 = gt_converter.convert()[0]
json_tracking_data2 = hyp_converter.convert()[0]

evaluator = MOTEvaluation(json_tracking_data1, json_tracking_data2, 5)

evaluator.evaluate()
evaluator.printResults()