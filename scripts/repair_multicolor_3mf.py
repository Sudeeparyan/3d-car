"""Preserve 3MF color volumes as one multipart object in PrusaSlicer.

Standard component assemblies can be imported as separate objects and dropped
independently. This rewrites only the 3MF container: vertices and faces are
preserved, materials are stored per triangle, and named-volume metadata records
face ranges. Other slicers may require the grouped STL fallback.
"""
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as ET

NS = 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
N = {'m': NS}
ET.register_namespace('', NS)
def tag(name):
    return '{' + NS + '}' + name

def ensure_multipart(path):
    path = Path(path)
    with ZipFile(path) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(contents['3D/3dmodel.model'])
    resources = root.find('m:resources', N)
    objects = resources.findall('m:object', N)
    if not any(obj.find('m:components', N) is not None for obj in objects):
        return
    parents = [obj for obj in objects if obj.find('m:components', N) is not None]
    if len(parents) != 1:
        raise ValueError('Expected one parent assembly')
    parent = parents[0]
    components = parent.findall('m:components/m:component', N)
    if any(component.get('transform') for component in components):
        raise ValueError('Expected common-coordinate identity components')
    ids = [component.get('objectid') for component in components]
    parts = [next(obj for obj in objects if obj.get('id') == oid) for oid in ids]
    root.set('xmlns:slic3rpe', 'http://schemas.slic3r.org/3mf/2017/06')
    meta = ET.Element(tag('metadata'), {'name':'slic3rpe:Version3mf'})
    meta.text = '1'
    root.insert(0, meta)
    description=root.find("m:metadata[@name='Description']",N)
    if description is not None:
        description.text='Aligned color volumes with PrusaSlicer multipart metadata. Assign each named part to its matching filament. No machine profile or G-code. Other slicers may require grouped STL import.'
    newobj=ET.Element(tag('object'),{'id':'2','type':'model','name':parent.get('name')})
    mesh=ET.SubElement(newobj,tag('mesh'))
    vertices=ET.SubElement(mesh,tag('vertices'))
    triangles=ET.SubElement(mesh,tag('triangles'))
    config=ET.Element('config')
    co=ET.SubElement(config,'object',{'id':'2','instances_count':'1'})
    ET.SubElement(co,'metadata',{'type':'object','key':'name','value':parent.get('name')})
    for part in parts:
        offset=len(vertices)
        first=len(triangles)
        for vertex in part.findall('m:mesh/m:vertices/m:vertex',N):
            vertices.append(deepcopy(vertex))
        for face in part.findall('m:mesh/m:triangles/m:triangle',N):
            tri=deepcopy(face)
            for key in ['v1','v2','v3']:
                tri.set(key,str(int(tri.get(key))+offset))
            tri.set('pid',part.get('pid'))
            tri.set('p1',part.get('pindex'))
            triangles.append(tri)
        volume=ET.SubElement(co,'volume',{'firstid':str(first),'lastid':str(len(triangles)-1)})
        for key,value in [('name',part.get('name')),('volume_type','ModelPart'),('matrix','1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1')]:
            ET.SubElement(volume,'metadata',{'type':'volume','key':key,'value':value})
        ET.SubElement(volume,'mesh',{'edges_fixed':'0','degenerate_facets':'0','facets_removed':'0','facets_reversed':'0','backwards_edges':'0'})
    for obj in objects:
        resources.remove(obj)
    resources.append(newobj)
    build=root.find('m:build',N)
    for item in list(build):
        build.remove(item)
    ET.SubElement(build,tag('item'),{'objectid':'2'})
    contents['3D/3dmodel.model']=ET.tostring(root,encoding='utf-8',xml_declaration=True)
    contents['Metadata/Slic3r_PE_model.config']=ET.tostring(config,encoding='utf-8',xml_declaration=True)
    types=ET.fromstring(contents['[Content_Types].xml'])
    type_ns='http://schemas.openxmlformats.org/package/2006/content-types'
    if not any(item.get('Extension')=='config' for item in types):
        ET.SubElement(types,'{'+type_ns+'}Default',{'Extension':'config','ContentType':'application/xml'})
    contents['[Content_Types].xml']=ET.tostring(types,encoding='utf-8',xml_declaration=True)
    with ZipFile(path,'w',ZIP_DEFLATED) as out:
        for name,content in contents.items():
            out.writestr(name,content)

if __name__=='__main__':
    import sys
    for arg in sys.argv[1:]:
        ensure_multipart(arg)
        print('Multipart container checked:',arg)
