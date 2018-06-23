import sys
import xml.etree.ElementTree as ET
from datetime import datetime
import os.path


"""Split TCX course into chunks.
"""


ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}


# Use this namespace when writing.
ET.register_namespace('', ns['tcx'])


def replace_element_children(old, new):
    old.clear()
    old.extend(new)

def str_to_datetime(s):
    return datetime.strptime(s, '%Y-%m-%dT%H:%M:%SZ')


def get_node_time(node):
    return str_to_datetime(node.find('./tcx:Time', ns).text)


def find_segments(tree, n_segments):
    track_points = tree.findall('.//tcx:Trackpoint', ns)
    track_points_chunks = list(chunks(track_points, n_segments))
    begin_points = [chunk[0] for chunk in track_points_chunks]
    end_points = [chunk[-1] for chunk in track_points_chunks]
    return list(zip(begin_points, end_points))


def get_path_to_chunk(path, idx):
    (location, filename) = os.path.split(path)
    (name, ext) = os.path.splitext(filename)
    chunk_filename = '{}-{}{}'.format(name, idx, ext)
    return os.path.join(location, chunk_filename)


def get_nodes_between(nodes, begin, end):
    return [node
            for node
            in nodes
            if get_node_time(begin) <= get_node_time(node) <= get_node_time(end)]


def write_tcx_chunk(path, idx, begin, end):
    tree = ET.parse(path)
    chunk_track_points = get_nodes_between(
        tree.findall('.//tcx:Trackpoint', ns), begin, end)
    chunk_course_points = get_nodes_between(
        tree.findall('.//tcx:CoursePoint', ns), begin, end)

    course = tree.find('.//tcx:Course', ns)

    course_name = course.find('./tcx:Name', ns)
    course_name.text = '{}-{}'.format(course_name.text, idx)

    lap = course.find('./tcx:Lap', ns)
    lap.find('./tcx:TotalTimeSeconds', ns).text = \
        str(int((get_node_time(end) - get_node_time(begin)).total_seconds()))
    replace_element_children(lap.find('./tcx:BeginPosition', ns), begin.find('./tcx:Position', ns))
    replace_element_children(lap.find('./tcx:EndPosition', ns), end.find('./tcx:Position', ns))

    track = course.find('./tcx:Track', ns)
    track.clear()
    track.extend(chunk_track_points)

    course_points = tree.findall('.//tcx:CoursePoint', ns)
    for child in course:
        if child in course_points and child not in chunk_course_points:
            course.remove(child)

    tree.write(get_path_to_chunk(path, idx),
               encoding='UTF-8',
               xml_declaration=True)


def split_tcx(path, n_segments):
    tree = ET.parse(path)
    segments = find_segments(tree, n_segments)
    for idx, (begin, end) in enumerate(segments):
        write_tcx_chunk(path, idx, begin, end)


# https://stackoverflow.com/a/2135920
def chunks(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))


if __name__ == '__main__':
    split_tcx(sys.argv[0])
