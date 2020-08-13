#!/usr/bin/env python

from copy import deepcopy
from pathlib import Path

import geojson
import shapely.geometry as sgeom

from repo import BroadcastAreasRepository

package_path = Path(__file__).resolve().parent


def convert_shape_to_feature(shape):
    return {
        "type": "Feature",
        "properties": {},
        "geometry": sgeom.mapping(shape),
    }


def simplify_polygon(series):
    polygon, *_holes = series  # discard holes

    approx_metres_to_degree = 111320
    # initially buffer (extend area past perimeter) by ~25m
    buffer_degrees = 500 / approx_metres_to_degree
    # initially simplify (snap to closest point) by ~25m
    simplify_degrees = 50.0 / approx_metres_to_degree

    starting_polygon = sgeom.LineString(polygon).buffer(buffer_degrees)
    simplified_polygon = None
    num_polys = len(polygon)
    last_num_polys = []
    while True:
        simplified_polygon = starting_polygon.simplify(simplify_degrees)
        simplified_polygon = [[c[0], c[1]] for c in simplified_polygon.exterior.coords]

        num_polys = len(simplified_polygon)
        simplify_degrees *= 2

        if num_polys <= 99 or last_num_polys[-3:] == [num_polys, num_polys, num_polys]:
            break

        last_num_polys.append(num_polys)

        print(".", end="", flush=True)  # noqa: T001

    return [simplified_polygon]


def simplify_geometry(feature):
    if feature["type"] == "Polygon":
        feature["coordinates"] = simplify_polygon(feature["coordinates"])
        return feature
    elif feature["type"] == "MultiPolygon":
        feature["coordinates"] = [
            simplify_polygon(polygon)
            for polygon in feature["coordinates"]
        ]
        return feature
    else:
        raise Exception("Unknown type: {}".format(feature["type"]))


repo = BroadcastAreasRepository()

repo.delete_db()
repo.create_tables()

simple_datasets = [
    ("Countries", "ctry19cd", "ctry19nm"),
    ("Counties and Unitary Authorities in England and Wales", "ctyua16cd", "ctyua16nm"),
]
for dataset_name, id_field, name_field in simple_datasets:
    filepath = package_path / "{}.geojson".format(dataset_name)

    dataset_id = id_field[:-2]
    dataset_geojson = geojson.loads(filepath.read_text())

    repo.insert_broadcast_area_library(dataset_id, dataset_name, False)

    for feature in dataset_geojson["features"]:
        f_id = dataset_id + "-" + feature["properties"][id_field]
        f_name = feature["properties"][name_field]

        print(f_name)  # noqa: T001

        simple_feature = deepcopy(feature)
        simple_feature["geometry"] = simplify_geometry(simple_feature["geometry"])

        repo.insert_broadcast_areas([[
            f_id, f_name,
            dataset_id, None,
            feature, simple_feature,
        ]])

# https://geoportal.statistics.gov.uk/datasets/wards-may-2020-boundaries-uk-bgc
# Converted to geojson manually from SHP because of GeoJSON download limits
wards_filepath = package_path / "Electoral Wards May 2020.geojson"

# http://geoportal.statistics.gov.uk/datasets/ward-to-westminster-parliamentary-constituency-to-local-authority-district-december-2019-lookup-in-the-united-kingdom/data
las_filepath = package_path / "Electoral Wards and Local Authorities 2020.geojson"

ward_code_to_la_mapping = {
    f["properties"]["WD19CD"]: f["properties"]["LAD19NM"]
    for f in geojson.loads(las_filepath.read_text())["features"]
}
ward_code_to_la_id_mapping = {
    f["properties"]["WD19CD"]: f["properties"]["LAD19CD"]
    for f in geojson.loads(las_filepath.read_text())["features"]
}

dataset_name = "Local authorities"
dataset_id = "wd20-lad20"
repo.insert_broadcast_area_library(dataset_id, dataset_name, True)

areas_to_add = []

for f in geojson.loads(wards_filepath.read_text())["features"]:
    ward_code = f["properties"]["wd20cd"]
    ward_name = f["properties"]["wd20nm"]
    ward_id = "wd20-" + ward_code

    print(ward_name)  # noqa: T001

    try:
        la_id = "lad20-" + ward_code_to_la_id_mapping[ward_code]
        la_name = ward_code_to_la_mapping[ward_code]

        sf = deepcopy(f)
        sf["geometry"] = simplify_geometry(sf["geometry"])

        areas_to_add.append([
            ward_id, ward_name,
            dataset_id, la_id,
            f, sf
        ])

    except KeyError:
        print("Skipping", ward_code, ward_name)  # noqa: T001

repo.insert_broadcast_areas(areas_to_add)
areas_to_add = []

las_filepath = package_path / "Local Authorities May 2020.geojson"

for feature in geojson.loads(las_filepath.read_text())["features"]:
    la_id = feature["properties"]["lad20cd"]
    group_name = feature["properties"]["lad20nm"]

    print(group_name)  # noqa: T001

    group_id = "lad20-" + la_id

    simple_feature = deepcopy(feature)
    simple_feature["geometry"] = simplify_geometry(simple_feature["geometry"])

    areas_to_add.append([
        group_id, group_name,
        dataset_id, None,
        feature, simple_feature
    ])

repo.insert_broadcast_areas(areas_to_add)
