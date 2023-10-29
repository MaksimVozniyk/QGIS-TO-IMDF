#TODO:
# 1. Change PATH variable to save IMDF project files inside .../project/IMDF path
# 2. Set branch for export several building in one project set building_dct variable
# 3. Separate address variables, building_dict to config_`project_name`.txt
# Line 116 The Ground Floor should be taken from building_dct variable with 0 ordinal!
# -----------------------------------------------------------------------------------------------------------------------
# Setting up path to IMDF.py folder
IMDF_PATH = r'C:\Users\OON\Documents\QGIS-TO-IMDF'

# Setting up path to folder to save outfiles (IMDF format)

PATH = r'C:\Users\OON\Documents\QGIS-TO-IMDF\TEST'
# Setting up full path to Service Account Credentials json file
CREDENTIALS_PATH = 'C:/Users/OON/Dropbox/TaxonomySpreedSheet-f9ebbf3ef5f8.json'

PROJECT_NAME = QgsProject.instance().fileInfo().baseName()
 
with open(f'{IMDF_PATH}/{PROJECT_NAME}.txt','r') as file:
    config = file.read()
config = [part.split('#')[0] for part in config.split('\n') if part[0] != '#']

# Setting up address variables for address
address_str = eval(config[0].split('=')[1])  # Formatted postal address, excluding suite/unit identifier
locality_str = eval(config[1].split('=')[1])  # Official locality (e.g. city, town) component of the postal address
province_str = eval(config[2].split('=')[1])  # Province (e.g. state, territory) component of the postal address
country_str = eval(config[3].split('=')[1])  # Country component of the postal address
postal_code = eval(config[4].split('=')[1])  # Mail sorting code extension associated with the postal code - it Could be None
# -----------------------------------------------------------------------------------------------------------------------
# Setting up venue name and category
category_venue = eval(config[5].split('=')[1])
name_venue = eval(config[6].split('=')[1])
# -----------------------------------------------------------------------------------------------------------------------
# Setting up building name, level and ordinal for this qgis project {Building:{Level: ordinal}}
building_dct = eval(config[7].split('=')[1])
# -----------------------------------------------------------------------------------------------------------------------
print('Got address_str = ', address_str)
print('Got locality_str = ', locality_str)
print('Got province_str = ', province_str)
print('Got country_str = ', country_str)
print('Got postal_code = ', postal_code)
print('Got category_venue = ', category_venue)
print('Got name_venue = ', name_venue)
print('Got building_dct = ', building_dct)
# -----------------------------------------------------------------------------------------------------------------------
import json
import os
import sys
from importlib import reload
from datetime import datetime
import gspread
import processing
from oauth2client.service_account import ServiceAccountCredentials


class ExportingHandler:
    def __init__(self, path):
        # self.path = os.path.dirname(__file__)
        self.path = path
        self.saving_folder = os.path.join(self.path, f'Generated {datetime.now().strftime("%H-%M-%S.%f %d-%m-%Y")}')

        self.unit_rows = {}
        self.fixture_rows = {}
        self.occupant_rows = {}
        self.amenity_rows = {}

        self.units = self.prepare_pattern_for_geojson_file("unit")
        self.anchors = self.prepare_pattern_for_geojson_file("anchor")
        self.occupants = self.prepare_pattern_for_geojson_file("occupant")
        self.amenities = self.prepare_pattern_for_geojson_file("amenity")
        self.openings = self.prepare_pattern_for_geojson_file("opening")
        self.fixtures = self.prepare_pattern_for_geojson_file("fixtures")
        self.footprints = self.prepare_pattern_for_geojson_file("footprint")
        self.buildings = self.prepare_pattern_for_geojson_file("building")
        self.levels = self.prepare_pattern_for_geojson_file("level")

        self.geojsons = []

        self.address = None
        self.venue = None

        self.manifest = {
                    "version" : "1.0.0",
                    "created" : "2023-10-25T15:05:54Z",
                    "language" : "en"
                }
    def break_table_into_settings_structure(self, table):
        for index, row in enumerate(table['Apple Unit Categories'], 1):
            if 59 > index > 1:
                self.unit_rows[row[0]] = self.combine_types_within_row(row)

            if 76 > index > 60:
                self.fixture_rows[row[0]] = self.combine_types_within_row(row)

            if 77 < index < 138:
                self.occupant_rows[row[0]] = self.combine_types_within_row(row)

            if 149 < index < 303:
                self.amenity_rows[row[0]] = self.combine_types_within_row(row)

    def combine_types_within_row(self, row):
        column_with_types = row[1]
        return [x.strip() for x in column_with_types.split(',')]

    def prepare_pattern_for_geojson_file(self, name):
        return {
            "features": [],
            "name": name,
            "type": "FeatureCollection"
        }
    def set_address(self, address):
        self.address = address
    def set_venue(self, venue):
        self.venue = venue

    def add_fixture(self, fixture):
        self.fixtures['features'].append(fixture.as_dict(False))

    def add_unit(self, unit):
        self.units['features'].append(unit.as_dict(False))

    def add_anchor(self, anchor):
        self.anchors['features'].append(anchor.as_dict(False))
    def add_occupant(self, occupant):
        self.occupants['features'].append(occupant.as_dict(False))
    def add_amenity(self, amenity):
        self.amenities['features'].append(amenity.as_dict(False))
    def add_opening(self, opening):
        self.openings['features'].append(opening.as_dict(False))
    def add_footprint(self, footprint):
        self.footprints['features'].append(footprint.as_dict(False))
    def add_building(self, building):
        self.buildings['features'].append(building.as_dict(False))
    def add_level(self, level):
        self.levels['features'].append(level.as_dict(False))

    def process_openings(self, layer, level):
        for feature in layer.getFeatures():
            opening = IMDF.Opening(feature, level)
            self.add_opening(opening)

    def dump_files(self):
        self.try_create_dir(self.saving_folder)
        self.update_geojsons_array()
        for geojson in self.geojsons:
            self.save_geojson(geojson)
        self.save_manifest()


    def try_create_dir(self, path):
        try:
            os.makedirs(path)
        except:
            pass

    def update_geojsons_array(self):
        self.geojsons.extend([self.address.as_dict(False),
                              self.venue.as_dict(False),
                              self.levels, self.buildings, self.footprints,
                              self.units, self.anchors, self.occupants,
                              self.amenities, self.openings, self.fixtures])

    def save_geojson(self, geojson):

        name = geojson.get('name', '')
        with open(f'{self.saving_folder}/{name}.geojson', 'w') as outfile:
            json.dump(geojson, outfile, indent=4)

    def save_manifest(self):
        with open(f'{self.saving_folder}/manifest.json', 'w') as outfile:
            json.dump(self.manifest, outfile, indent=4)


def process_features(features, level, exporting_handler):
    for feature in features:

        fixture = create_fixture(feature, exporting_handler)
        if fixture:
            exporting_handler.add_fixture(fixture)
            continue

        unit = create_unit(feature, level, exporting_handler)
        exporting_handler.add_unit(unit)
        print(f'{unit.category = }')
        if unit.category == 'room':

            anchor = create_anchor(feature, unit, exporting_handler)
            occupant = create_occupant(feature, anchor, exporting_handler)
            print("unit.category == 'room'", anchor, occupant)
            if occupant:
                exporting_handler.add_anchor(anchor)
                exporting_handler.add_occupant(occupant)

        amenity = create_amenity(feature, unit, exporting_handler)
        if amenity:
            exporting_handler.add_amenity(amenity)

def extract_feature_category(feature, categories):
    tid = feature.attribute('tid')
    if not isinstance(tid, str):
        tid = str(tid)
    for category, tids in categories.items():
        if tid in tids:
            return category
    for category, tids in categories.items():
        if tids == ['all other']:
            return 'room'

def create_fixture(feature, exporting_handler):
    category_fixture = extract_feature_category(feature, exporting_handler.fixture_rows)
    if category_fixture:
        fixture = IMDF.Fixture(feature, level, category_fixture)
        return fixture

def create_unit(feature, level, exporting_handler):
    category_unit = extract_feature_category(feature, exporting_handler.unit_rows)
    unit = IMDF.Unit(feature, level, category_unit)
    return unit

def create_anchor(feature, unit, exporting_handler):
    anchor = IMDF.Anchor(feature, unit, exporting_handler.address)
    return anchor

def create_occupant(feature, anchor, exporting_handler):
    category_occupant = extract_feature_category(feature, exporting_handler.occupant_rows)
    if category_occupant:
        occupant = IMDF.Occupant(feature, anchor, category_occupant)
        return occupant

def create_amenity(feature, unit, exporting_handler):
    category = extract_feature_category(feature, exporting_handler.amenity_rows)
    if category:
        amenity = IMDF.Amenity(unit, category, exporting_handler.address)
        return amenity


def prepare_layer_for_processing(layer):
    layer = processing.run("native:multiparttosingleparts",
                           {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    layer = processing.run("native:reprojectlayer", {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT',
                                                     'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']

    layer = processing.run("native:removenullgeometries",
                           {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    return layer



if IMDF_PATH not in sys.path:
    sys.path.append(IMDF_PATH)
import IMDF
reload(IMDF)  # Reload IMDF classes after changing
def set_json_keys(name):
    dct = {}
    dct["features"] = []
    dct["name"] = name
    dct["type"] = "FeatureCollection"
    return dct
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)

gc = gspread.authorize(credentials)
wks = gc.open('Pointr Taxonomy v2')
unit_rows = {}  # Handle taxonomy spreedsheet
fixture_rows = {}
occupant_rows = {}
amenity_rows = {}
sheets_dict = {}

for sheet_n in wks.worksheets():
    sheet = sheet_n.get_all_values()
    sheets_dict[sheet_n.title] = sheet
for index_in_sheet, row in enumerate(sheets_dict['Apple Unit Categories'], 1):
    if 59 > index_in_sheet > 1:
        unit_rows[row[0]] = [x.strip() for x in row[1].split(',')]
    if 76 > index_in_sheet > 60:
        fixture_rows[row[0]] = [x.strip() for x in row[1].split(',')]
    if 77 < index_in_sheet < 138:
        occupant_rows[row[0]] = [x.strip() for x in row[1].split(',')]
    if 149 < index_in_sheet < 303:
        amenity_rows[row[0]] = [x.strip() for x in row[1].split(',')]


# 0 - Creating Address object
address = IMDF.Address(address_str, locality_str, province_str, country_str, postal_code)
# 1 - Venue +
# If there are more then 1 building there should venue layer exist in this project and venue polygon should occupies all buildings
if len(building_dct) == 1:
    if not QgsProject.instance().mapLayersByName('venue'):  # If the venue layer doesn't exist it would be created from GF
        layer_venue = QgsProject.instance().mapLayersByName('GF')[0]
        layer_venue = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': 0.0001, 'END_CAP_STYLE': 0, 'INPUT': layer_venue, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})
        layer_venue = processing.run("native:dissolve", {'FIELD': [], 'INPUT': layer_venue['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})
        layer_venue = layer_venue['OUTPUT']
    else:  # otherwise we use Venue layer
        layer_venue = QgsProject.instance().mapLayersByName('venue')[0]
else:  # otherwise we use Venue layer
    try:
        layer_venue = QgsProject.instance().mapLayersByName('venue')[0]
    except:
        int('There are no venue layer in this project. It should exist because there are more than 1 building')
layer_venue = processing.run("native:reprojectlayer", {'INPUT': layer_venue, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
layer_venue = layer_venue['OUTPUT']
feature_venue = list(layer_venue.getFeatures())[0]
venue = IMDF.Venue(feature_venue, category=category_venue, name=name_venue)
venue.assign_address_id(address.uid)
# 2 - Footprint +
# Subterranean
# Ground
footprints = set_json_keys("footprint")
buildings = set_json_keys("building")
levels = set_json_keys("level")
units = set_json_keys("unit")
anchors = set_json_keys("anchor")
occupants = set_json_keys("occupant")
amenities = set_json_keys("amenity")
openings = set_json_keys("opening")
fixtures = set_json_keys("fixtures")

exporting_handler = ExportingHandler(IMDF_PATH)
exporting_handler.break_table_into_settings_structure(sheets_dict)
exporting_handler.set_address(address)
exporting_handler.set_venue(venue)

for b in building_dct.keys():
    for l in building_dct[b].keys():
        # Searching ordinal 0 in building levels to create a footprint for each building
        if building_dct[b][l] == 0:
            layer_gf = QgsProject.instance().mapLayersByName(l)[0]
            # branching for several buildings
            if len(building_dct) > 1:
                layer_gf.selectByExpression(f"\"building\" = '{b}'")
                reference_layer = processing.run("native:saveselectedfeatures",
                                                 {'INPUT': layer_gf, 'OUTPUT': 'TEMPORARY_OUTPUT'})
                reference_layer = reference_layer['OUTPUT']
            else:
                reference_layer = layer_gf
            layer_gf = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': 0.02, 'END_CAP_STYLE': 0, 'INPUT': reference_layer, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
            layer_gf = processing.run("native:fixgeometries", { 'INPUT' : layer_gf, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']

            _layer_gf = processing.run("native:dissolve", {'FIELD': [], 'INPUT': layer_gf, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
            footprint_layer = processing.run("native:deleteholes", {'INPUT': _layer_gf, 'MIN_AREA': 0.0, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
            footprint_layer = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': -0.02, 'END_CAP_STYLE': 0,'INPUT': footprint_layer, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2,'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
            footprint_layer = processing.run("native:reprojectlayer", {'INPUT': footprint_layer, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
            feature_footprint = list(footprint_layer['OUTPUT'].getFeatures())[0]
            footprint = IMDF.Footprint(feature_footprint)
            # 3 Building
            building = IMDF.Building(footprint)


    footprints["features"].append(footprint.as_dict(False))

    building.assign_address_id(address.uid)
    building.assign_name(b)

    buildings["features"].append(building.as_dict(False))
    exporting_handler.add_footprint(footprint)
    exporting_handler.add_building(building)




    for level_name in building_dct[b].keys():
        layer_level_input = QgsProject.instance().mapLayersByName(level_name)[0]
        # branching for several buildings
        if len(building_dct) > 1:
            layer_level_input.selectByExpression(f"\"building\" = '{b}'")
            reference_layer = processing.run("native:saveselectedfeatures", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})
            reference_layer = reference_layer['OUTPUT']
        else:
            reference_layer = layer_level_input

        # Level
        layer_level = processing.run("native:fixgeometries", { 'INPUT' : reference_layer, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        layer_level = processing.run("native:buffer", {'DISSOLVE': True, 'DISTANCE': 0.02, 'END_CAP_STYLE': 0, 'INPUT': layer_level, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
        layer_level = processing.run("native:buffer",{'DISSOLVE': True, 'DISTANCE': -0.02, 'END_CAP_STYLE': 0, 'INPUT': layer_level,'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
        layer_level = processing.run("native:deleteholes", {'INPUT': layer_level, 'MIN_AREA': 0.0, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})['OUTPUT']
        layer_level = processing.run("native:fixgeometries", {'INPUT': layer_level, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
        layer_level_4326 = processing.run("native:reprojectlayer", {'INPUT': layer_level, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
        feature = list(layer_level_4326['OUTPUT'].getFeatures())[0]
        ordinal = building_dct[b][level_name]
        level = IMDF.Level(feature, level_name, building, address, ordinal=ordinal)
        levels["features"].append(level.as_dict(False))


        # Features
        layer_level_input = processing.run("native:fixgeometries", {'INPUT': reference_layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
        layer_level_input = processing.run("native:multiparttosingleparts", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT' })['OUTPUT']

        # Test
        layer_level_input = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': -0.001, 'END_CAP_STYLE': 1,
                                                             'INPUT': layer_level_input, 'JOIN_STYLE': 1,
                                                             'MITER_LIMIT': 2,
                                                             'OUTPUT': 'memory:', 'SEGMENTS': 5})['OUTPUT']

        layer_level_input = processing.run("native:snapgeometries", {'BEHAVIOR': 0,
                                                                     'INPUT': layer_level_input,
                                                                     'OUTPUT': 'TEMPORARY_OUTPUT',
                                                                     'REFERENCE_LAYER': layer_level,
                                                                     'TOLERANCE': 0.015})['OUTPUT']
        layer_level_input = processing.run("native:snapgeometries", {'BEHAVIOR': 0,
                                                                     'INPUT': layer_level_input,
                                                                     'OUTPUT': 'TEMPORARY_OUTPUT',
                                                                     'REFERENCE_LAYER': layer_level_input,
                                                                     'TOLERANCE': 0.0075})['OUTPUT']


        layer_level_input = processing.run("native:reprojectlayer", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']
        layer_level_input = processing.run("native:removenullgeometries", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']




        exporting_handler.add_level(level)
        process_features(layer_level_input.getFeatures(), level, exporting_handler)



        # Working with openings:
        if QgsProject.instance().mapLayersByName(f'{level_name}_openings_single') != []:
            openings_layer = QgsProject.instance().mapLayersByName(f'{level_name}_openings_single') [0]
            openings_layer = prepare_layer_for_processing(openings_layer)

            for feature_opening in openings_layer.getFeatures():
                opening = IMDF.Opening(feature_opening, level)
                openings["features"].append(opening.as_dict(False))

            exporting_handler.process_openings(openings_layer, level)
        else:
            print('Exporting of "openings" layer is failed')





exporting_handler.dump_files()