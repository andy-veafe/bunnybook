import os
import sys

sys.path.append(os.getcwd())

print(sys.argv)
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        exec(f.read())
except Exception as e:
    print("无法运行：", sys.argv[1])
    raise e
