import sys
from pathlib import Path
sys.path.insert(0,'/home/gordon/.local/opt/GMAT/R2026a/bin')
import gmatpy as g
folder=Path(sys.argv[1]);name=sys.argv[2]
g.Setup(str(folder/(name+'.console.startup.txt')))
assert g.LoadScript(str(folder/(name+'.script')))
print('SYNTAX CHECK PASSED; MISSION NOT RUN:',name)
g.Clear()
