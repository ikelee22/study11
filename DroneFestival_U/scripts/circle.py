import time
import math
import numpy as np

#print('command')
time.sleep(0.5)
radius=50
f = open('circleScript','w')
#print('order가 종료되었습니다.')
for i in range(0,360,1):
    th=math.radians(i)
    x1=math.cos(th)
    y1=math.sin(th)
    x2=math.cos(math.radians(i+1))
    y2=math.sin(math.radians(i+1))
    v1 = np.array([x1,y1])
    v2 = np.array([x2,y2])
    v3 = v2 -v1
    v3 = v3 / np.linalg.norm(v3)*10
    print('rc %f %f %f %f'% (v3[0], v3[1], 0, 0))
    print('sleep 0.02')
    f.write('rc %f %f %f %f\n' % (v3[0], v3[1], 0, 0))
    f.write('sleep 0.02\n')
                                                                    

