{"filter":false,"title":"source.js","tooltip":"/webui/util/source/server/source.js","undoManager":{"mark":27,"position":27,"stack":[[{"start":{"row":54,"column":5},"end":{"row":54,"column":6},"action":"insert","lines":[","],"id":198}],[{"start":{"row":54,"column":6},"end":{"row":55,"column":0},"action":"insert","lines":["",""],"id":199},{"start":{"row":55,"column":0},"end":{"row":55,"column":4},"action":"insert","lines":["    "]}],[{"start":{"row":55,"column":4},"end":{"row":69,"column":5},"action":"insert","lines":[" pydoc: function readpydoc(file){","        var future = new Future();","        ","        file = file.replace(/[\\/|\\\\]/g, \"SLASH\") // Kill slashes","        ","        exec(path + \"Documentor.py \" + path + file, {cwd: path}, function(err, stdout, stderr){","            if (err){","                future.throw(err)","            } else {","                future.return(stdout.toString());  ","            }","          ","        })","        return future.wait();","    }"],"id":200}],[{"start":{"row":55,"column":4},"end":{"row":55,"column":5},"action":"remove","lines":[" "],"id":201}],[{"start":{"row":55,"column":6},"end":{"row":55,"column":9},"action":"remove","lines":["doc"],"id":202},{"start":{"row":55,"column":6},"end":{"row":55,"column":7},"action":"insert","lines":["h"]}],[{"start":{"row":55,"column":7},"end":{"row":55,"column":8},"action":"insert","lines":["e"],"id":203}],[{"start":{"row":55,"column":8},"end":{"row":55,"column":9},"action":"insert","lines":["l"],"id":204}],[{"start":{"row":55,"column":9},"end":{"row":55,"column":10},"action":"insert","lines":["p"],"id":205}],[{"start":{"row":60,"column":13},"end":{"row":60,"column":39},"action":"remove","lines":["path + \"Documentor.py \" + "],"id":206}],[{"start":{"row":60,"column":24},"end":{"row":60,"column":25},"action":"insert","lines":[" "],"id":207}],[{"start":{"row":60,"column":25},"end":{"row":60,"column":26},"action":"insert","lines":["+"],"id":208}],[{"start":{"row":60,"column":26},"end":{"row":60,"column":27},"action":"insert","lines":[" "],"id":209}],[{"start":{"row":60,"column":27},"end":{"row":60,"column":29},"action":"insert","lines":["\"\""],"id":210}],[{"start":{"row":60,"column":28},"end":{"row":60,"column":29},"action":"insert","lines":[" "],"id":211}],[{"start":{"row":60,"column":29},"end":{"row":60,"column":30},"action":"insert","lines":["_"],"id":212}],[{"start":{"row":60,"column":29},"end":{"row":60,"column":30},"action":"remove","lines":["_"],"id":213}],[{"start":{"row":60,"column":30},"end":{"row":60,"column":31},"action":"insert","lines":[" "],"id":214}],[{"start":{"row":60,"column":31},"end":{"row":60,"column":32},"action":"insert","lines":["+"],"id":215}],[{"start":{"row":60,"column":32},"end":{"row":60,"column":33},"action":"insert","lines":[" "],"id":216}],[{"start":{"row":60,"column":32},"end":{"row":60,"column":33},"action":"remove","lines":[" "],"id":217}],[{"start":{"row":60,"column":31},"end":{"row":60,"column":32},"action":"remove","lines":["+"],"id":218}],[{"start":{"row":60,"column":30},"end":{"row":60,"column":31},"action":"remove","lines":[" "],"id":219}],[{"start":{"row":60,"column":29},"end":{"row":60,"column":30},"action":"insert","lines":["-"],"id":220}],[{"start":{"row":60,"column":30},"end":{"row":60,"column":31},"action":"insert","lines":["-"],"id":221}],[{"start":{"row":60,"column":31},"end":{"row":60,"column":32},"action":"insert","lines":["h"],"id":222}],[{"start":{"row":60,"column":32},"end":{"row":60,"column":33},"action":"insert","lines":["e"],"id":223}],[{"start":{"row":60,"column":33},"end":{"row":60,"column":34},"action":"insert","lines":["l"],"id":224}],[{"start":{"row":60,"column":34},"end":{"row":60,"column":35},"action":"insert","lines":["p"],"id":225}]]},"ace":{"folds":[],"scrolltop":690.9995727539062,"scrollleft":0,"selection":{"start":{"row":61,"column":21},"end":{"row":61,"column":21},"isBackwards":false},"options":{"guessTabSize":true,"useWrapMode":false,"wrapToView":true},"firstLineState":{"row":28,"state":"start","mode":"ace/mode/javascript"}},"timestamp":1498646743162,"hash":"555a0ab009f871ef65e43983bc6c95a7edb8cdf1"}