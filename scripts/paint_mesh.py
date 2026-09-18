"""Face-material painting guide on the exact printable mesh (no texture illusions)."""
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree, ConvexHull
import trimesh, json
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work'
body=trimesh.load_mesh(W/'body_assembled.stl')
# Subdivide planar triangles only to place paint edges cleanly; this changes no
# surface positions and does not add detail absent from the printable STL.
v,f=trimesh.remesh.subdivide_to_size(body.vertices,body.faces,max_edge=.65,max_iter=16)
body=trimesh.Trimesh(v,f,process=True)
print('Paint surface triangles',len(f),flush=True)
raw=trimesh.load_mesh(ROOT/'reference_assets/thingiverse_3192801/files/mustangBodyOnly.stl')
source=raw.split(only_watertight=False,repair=False)
centers=[];ids=[]
black={1,2,5,7,9,10,11,12,13,22,23,24,25,26,27,31,37,46,88,137,138}
red={32,34,36,38,40,42}
silver={17,28,30,131,132,133,134,145}
for i,p in enumerate(source):
    c=p.triangles_center.copy();c[:,1]-=17.805959701538086;c[:,2]+=23.417420;c*=160/140
    centers.append(c)
    mat=1 if i in black else 2 if i in red else 3 if i in silver else 0
    ids.extend([mat]*len(c))
tree=cKDTree(np.vstack(centers));dist,near=tree.query(body.triangles_center)
ids=np.array(ids);colors=np.zeros(len(body.faces),dtype=int)
x,y,z=body.triangles_center.T;n=body.face_normals
def projected(index,axes):
    p=source[index].vertices.copy();p[:,1]-=17.805959701538086;p[:,2]+=23.417420;p*=160/140
    h=ConvexHull(p[:,axes]); eq=h.equations
    q=body.triangles_center[:,axes]
    result=np.zeros(len(q),dtype=bool)
    for j in range(0,len(q),20000):result[j:j+20000]=np.all(q[j:j+20000]@eq[:,:2].T+eq[:,2]<=.03,axis=1)
    return result
# Coherent paint regions follow the source panel outlines. Point-to-centroid
# transfer is deliberately avoided: large source triangles made it speckled.
colors[projected(22,[0,2])&(abs(y)>20)&(z>31)&(abs(n[:,1])>.2)]=1
colors[projected(5,[0,1])&(z>31)&(n[:,2]>.15)]=1
colors[projected(1,[1,2])&(x<-68)&(n[:,0]<-.15)]=1
colors[projected(24,[1,2])&(x<-68)&(n[:,0]<-.1)]=1
colors[projected(27,[1,2])&(x>70)&(n[:,0]>.1)]=1
colors[(x>-66.95)&(x<-60.45)&(abs(abs(y)-12.6)<2.85)&(z>29)]=1
for i in [28,30]:colors[projected(i,[0,1])&(z>22.5)&(z<27.6)]=1
for i in [31,37]:colors[projected(i,[1,2])&(x>67)&(n[:,0]>.1)]=1
for i in [32,34,36,38,40,42]:colors[projected(i,[1,2])&(x>67)&(n[:,0]>.1)]=2
# Front windscreen is joined to the main source body, unlike side/rear glazing.
wind=(x>-24.5)&(x<-5.1)&(z>34.2)&(abs(y)<24)&(n[:,0]<-.2)&(n[:,2]>.3)
colors[wind]=1
# Reinforced mirror heads and arms.
colors[(x>-20)&(x<-8)&(abs(y)>25.8)&(z>31.5)&(z<37.5)]=1
# Spoiler top follows the curved rear edge. All added lip surfaces are dark.
t=(np.minimum(abs(y),28)/28)**2
colors[(x>68.6-4*t)&(x<74.2-4*t)&(abs(y)<28.2)&(z>32.6-1.7*t)]=1
# Paint-only rocker stripe with the three diagonal interruptions in the photos.
stripe=(x>-35)&(x<31)&(z>9.5)&(z<13.8)&(abs(y)>26)
diagonal=x-.7*(z-9.5)
stripe&=~(((diagonal>-32)&(diagonal<-30))|((diagonal>-26)&(diagonal<-24))|((diagonal>-20)&(diagonal<-18)))
colors[stripe]=1
colors[(z<9.1)&(abs(y)>24)]=1
colors[(x<-62)&(z<10)]=1
colors[(x>-33.0)&(x<-28.4)&(z>21.7)&(z<24.3)&(abs(y)>31.15)]=1
# Gluing pads deliberately unpainted in the instructional view.
np.savez_compressed(W/'body_painted.npz',vertices=body.vertices,faces=body.faces,material=colors)

wheel=trimesh.load_mesh(W/'wheel_master.stl')
x,y,z=wheel.triangles_center.T;r=np.sqrt(x*x+y*y)
colors=np.ones(len(wheel.faces),dtype=int)
colors[(r<8.2)&(z>7)]=4
colors[(r>8.85)&(r<9.85)&(z>7.8)]=3
colors[(r<9.6)&(z>7.7)]=3
colors[(x>-7.4)&(x<-4.8)&(y>-1.9)&(y<4.3)&(z>7.05)&(z<7.96)]=2
colors[(r<2.45)&(z>8.45)]=3
np.savez_compressed(W/'wheel_painted.npz',vertices=wheel.vertices,faces=wheel.faces,material=colors)
print('PAINT_DATA_COMPLETE')
