import os
import re
basedir = '/Volumes/0973111473/Paulis_annotation2/2_mammo__3 New'
for fn in os.listdir(basedir):
  if not os.path.isdir(os.path.join(basedir, fn)):
    continue # Not a directory
  x = re.findall("^PAT[0-9][0-9][0-9]", fn)
  print(x)
  y=fn.replace(x[0],'PAT')
  print(y,fn)
  os.rename(os.path.join(basedir, fn),
            os.path.join(basedir, y))