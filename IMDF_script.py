#TODO:
# 1. Change PATH variable to save IMDF project files inside .../project/IMDF path
# 2. Set branch for export several building in one project set building_dct variable
# 3. Separate address variables, building_dict to config_`project_name`.txt
# Line 116 The Ground Floor should be taken from building_dct variable with 0 ordinal!
# -----------------------------------------------------------------------------------------------------------------------
# Setting up path to IMDF.py folder
IMDF_PATH = r'C:\Users\OON\Documents\QGIS-TO-IMDF'

# Setting up full path to Service Account Credentials json file
CREDENTIALS_PATH = 'C:/Users/OON/Dropbox/TaxonomySpreedSheet-f9ebbf3ef5f8.json'


import json
import os
import sys
from importlib import reload
from datetime import datetime
import gspread
import processing
from oauth2client.service_account import ServiceAccountCredentials
from shapely.geometry import Polygon, shape

if IMDF_PATH not in sys.path:
    sys.path.append(IMDF_PATH)
import IMDF
reload(IMDF)  # Reload IMDF classes after changing

class ProjectConfigurations:
    def __init__(self):
        prjfi = QFileInfo(QgsProject.instance().fileName())
        self.project_path = prjfi.absolutePath()
        self.project_name = prjfi.baseName()
        self.config = os.path.join(self.project_path, self.project_name + '.json')
        self.saving_folder_path = os.path.join(os.path.dirname(self.project_path), f'Generated {datetime.now().strftime("%H-%M-%S.%f %d-%m-%Y")}')
        self.config_data = []

        self.address_str = ''
        self.locality_str = ''
        self.province_str = ''
        self.country_str = ''
        self.postal_code = ''
        self.category_venue = ''
        self.name_venue = ''
        self.building_dct = ''

        self.read_config_data()
        self.setup_configurations()

    def read_config_data(self):
        with open(f'{self.project_path}/{self.project_name}.txt','r') as file:
            config = file.read()
        self.config_data = [part.split('#')[0] for part in config.split('\n') if part[0] != '#']

    def setup_configurations(self):
        # Setting up address variables for address
        self.address_str = eval(self.config_data[0].split('=')[1])  # Formatted postal address, excluding suite/unit identifier
        self.locality_str = eval(
            self.config_data[1].split('=')[1])  # Official locality (e.g. city, town) component of the postal address
        self.province_str = eval(self.config_data[2].split('=')[1])  # Province (e.g. state, territory) component of the postal address
        self.country_str = eval(self.config_data[3].split('=')[1])  # Country component of the postal address
        self.postal_code = eval(
            self.config_data[4].split('=')[1])  # Mail sorting code extension associated with the postal code - it Could be None
        # -----------------------------------------------------------------------------------------------------------------------
        # Setting up venue name and category
        self.category_venue = eval(self.config_data[5].split('=')[1])
        self.name_venue = eval(self.config_data[6].split('=')[1])
        # -----------------------------------------------------------------------------------------------------------------------
        # Setting up building name, level and ordinal for this qgis project {Building:{Level: ordinal}}
        self.building_dct = eval(self.config_data[7].split('=')[1])



class ExportingHandler(ProjectConfigurations):
    def __init__(self, imdf_folder_path):
        super().__init__()

        self.unit_rows = {}
        self.fixture_rows = {}
        self.occupant_rows = {}
        self.amenity_rows = {}
        self.kiosk_rows = {}
        self.section_rows = {}

        self.units = self.prepare_pattern_for_geojson_file("unit")
        self.anchors = self.prepare_pattern_for_geojson_file("anchor")
        self.occupants = self.prepare_pattern_for_geojson_file("occupant")
        self.amenities = self.prepare_pattern_for_geojson_file("amenity")
        self.openings = self.prepare_pattern_for_geojson_file("opening")
        self.fixtures = self.prepare_pattern_for_geojson_file("fixtures")
        self.kiosks = self.prepare_pattern_for_geojson_file("kiosk")
        self.sections = self.prepare_pattern_for_geojson_file("section")
        self.footprints = self.prepare_pattern_for_geojson_file("footprint")
        self.buildings = self.prepare_pattern_for_geojson_file("building")
        self.levels = self.prepare_pattern_for_geojson_file("level")

        self.geojsons = []

        self.address = None
        self.venue = None

        self.manifest = {
                    "version" : "1.0.0",
                    "created" : "2023-11-25T15:05:54Z",
                    "language" : "en"
                }
    def break_table_into_settings_structure(self, table):
        for index, row in enumerate(table['Apple Unit Categories'], 1):
            if 59 > index > 1:
                self.unit_rows[row[0]] = self.combine_types_within_row(row)

            if 76 > index > 60:
                self.fixture_rows[row[0]] = self.combine_types_within_row(row)

            if 77 < index < 142:
                self.occupant_rows[row[0]] = self.combine_types_within_row(row)

            if 153 < index < 307:
                self.amenity_rows[row[0]] = self.combine_types_within_row(row)

            if 308 < index < 310:
                self.kiosk_rows[row[0]] = self.combine_types_within_row(row)

            if 311 < index < 313:
                self.section_rows[row[0]] = self.combine_types_within_row(row)

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

    def add_kiosk(self, kiosk):
        self.kiosks['features'].append(kiosk.as_dict(False))

    def add_section(self, section):
        self.sections['features'].append(section.as_dict(False))

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
        self.try_create_dir(self.saving_folder_path)
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
                              self.amenities, self.openings, self.fixtures, self.kiosks,
                              self.sections])

    def save_geojson(self, geojson):

        name = geojson.get('name', '')
        with open(f'{self.saving_folder_path}/{name}.geojson', 'w') as outfile:
            json.dump(geojson, outfile, indent=4)

    def save_manifest(self):
        with open(f'{self.saving_folder_path}/manifest.json', 'w') as outfile:
            json.dump(self.manifest, outfile, indent=4)


def process_features(features, level, exporting_handler):
    for feature in features:

        if extract_feature_category(feature.attribute('tid'), exporting_handler.fixture_rows) or \
                extract_feature_category(feature.attribute('tid'), exporting_handler.kiosk_rows):
            continue

        if extract_feature_category(feature.attribute('tid'), exporting_handler.section_rows):
            section = create_section(feature, level)
            exporting_handler.add_section(section)
            continue

        unit = create_unit(feature, feature.attribute('tid'), level, exporting_handler)
        exporting_handler.add_unit(unit)

        if unit.category == 'room':
            generate_occupant(feature, feature.attribute('tid'), unit.uid, exporting_handler)

        amenity = create_amenity(feature.attribute('tid'), unit, exporting_handler)
        if amenity:
            exporting_handler.add_amenity(amenity)

    for feature in features:
        fixture = create_fixture(feature, feature.attribute('tid'), exporting_handler)
        if fixture:
            exporting_handler.add_fixture(fixture)
            continue

        kiosk = create_kiosk(feature, feature.attribute('tid'), exporting_handler)
        if kiosk:
            unit_geojson = get_unit(exporting_handler.units, kiosk, level.uid)
            # print('anchor generat', feature.attribute('occupant_tid'), unit_geojson.get('id'))
            anchor = generate_occupant(feature, feature.attribute('occupant_tid'), unit_geojson.get('id'), exporting_handler)
            # print('anchor', anchor)
            kiosk.set_anchor(anchor)
            exporting_handler.add_kiosk(kiosk)
            continue

def generate_occupant(feature, tid, unit_uid, exporting_handler):
    anchor = create_anchor(feature, unit_uid, exporting_handler)
    occupant = create_occupant(feature, tid, anchor, exporting_handler)

    if occupant:
        exporting_handler.add_anchor(anchor)
        exporting_handler.add_occupant(occupant)
        return anchor

def create_anchor(feature, unit_uid, exporting_handler):
    anchor = IMDF.Anchor(feature, unit_uid, exporting_handler.address)
    return anchor

def create_occupant(feature, tid, anchor, exporting_handler):
    category_occupant = extract_feature_category(tid, exporting_handler.occupant_rows)
    if category_occupant:
        occupant = IMDF.Occupant(feature, anchor, category_occupant)
        return occupant
def get_unit(units: list, imdf_feature, level_id: str) -> dict:

    if not isinstance(imdf_feature, QgsFeature):
        qgs_feature = create_qgs_feature_from_imdf_feature(imdf_feature.as_dict(False))
    else:
        qgs_feature = imdf_feature
    # print('qgs_feature', qgs_feature )
    for unit in units['features']:
        unit_feature = create_qgs_feature_from_imdf_feature(unit)

        if qgs_feature.geometry().within(unit_feature.geometry()) and level_id == unit['properties']['level_id']:
            # print('LEVEL', level_id, unit['properties']['level_id'])
            # print('WITHIN unit, imdf_feature', unit.get('id'))
            return unit

    print('Feature ', qgs_feature.geometry().asJson(), 'not within any unit')

def create_qgs_feature_from_imdf_feature(imdf_feature) -> QgsFeature:
    feature = QgsFeature()
    # print('imdf_feature', imdf_feature)
    geom = shape(imdf_feature.get('geometry'))
    feature.setGeometry(QgsGeometry.fromWkt(geom.wkt))

    fields = QgsFields()
    fields.append(QgsField('name', QVariant.String))
    fields.append(QgsField('fid_PC', QVariant.String))

    feature.setFields(fields)
    feature.setAttribute('name', 'Test')
    feature.setAttribute('fid_PC', imdf_feature["id"])

    return feature


def extract_feature_category(tid, categories):

    if not isinstance(tid, str):
        tid = str(tid)
    # print(tid, type(tid), categories)
    for category, tids in categories.items():
        if tid in tids:
            return category
    for category, tids in categories.items():
        if tids == ['all other']:
            return 'room'

def create_fixture(feature, tid,  exporting_handler):
    category_fixture = extract_feature_category(tid, exporting_handler.fixture_rows)
    if category_fixture:
        fixture = IMDF.Fixture(feature, level, category_fixture)
        return fixture

def create_kiosk(feature, tid, exporting_handler):
    category_kiosk = extract_feature_category(tid, exporting_handler.kiosk_rows)
    # print('category_kiosk', category_kiosk, exporting_handler.kiosk_rows)
    if category_kiosk:
        kiosk = IMDF.Kiosk(feature, level)
        return kiosk

def create_unit(feature, tid, level, exporting_handler):
    category_unit = extract_feature_category(tid, exporting_handler.unit_rows)
    # print('category_unit', category_unit)
    unit = IMDF.Unit(feature, level.uid, category_unit)
    return unit

def create_section(feature, level):
    section = IMDF.Section(feature, level.uid)
    return section



def create_amenity(tid, unit, exporting_handler, name=None, centroid=None):
    category = extract_feature_category(tid, exporting_handler.amenity_rows)
    if category:
        amenity = IMDF.Amenity(unit, category, exporting_handler.address, name=name, centroid=centroid)
        return amenity


def prepare_layer_for_processing(layer, layer_level_input):
    layer = processing.run("native:multiparttosingleparts",
                           {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    layer = processing.run("native:reprojectlayer", {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT',
                                                     'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']

    layer = processing.run("native:removenullgeometries",
                           {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    
    layer_level_input = processing.run("native:removenullgeometries",
                           {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    layer_level_input = processing.run("native:fixgeometries",
                           {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    
    layer = processing.run("native:snapgeometries", {'BEHAVIOR' : 0, 'INPUT' : layer , 
                                           'OUTPUT' : 'TEMPORARY_OUTPUT', 
                                           'REFERENCE_LAYER' : layer_level_input,
                                           'TOLERANCE' : 0.00000007 })['OUTPUT']
    
    return layer

def create_building_layer(layer: QgsVectorLayer) -> QgsVectorLayer:
    layer = processing.run("native:buffer",
                              {'DISSOLVE': False, 'DISTANCE': 0.02, 'END_CAP_STYLE': 0, 'INPUT': layer,
                               'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
    layer = processing.run("native:fixgeometries", {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']

    layer = processing.run("native:dissolve", {'FIELD': [], 'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    layer = processing.run("native:deleteholes", {'INPUT': layer, 'MIN_AREA': 0.0, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
    layer = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': -0.02, 'END_CAP_STYLE': 0,
                                                       'INPUT': layer, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2,
                                                       'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
    layer = processing.run("native:reprojectlayer", {'INPUT': layer, 'OUTPUT': 'TEMPORARY_OUTPUT',
                                                               'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']
    return layer
def generate_footprint(layer):
    building_layer = create_building_layer(layer)
    feature_footprint = list(building_layer.getFeatures())[0]
    return IMDF.Footprint(feature_footprint)

def create_footprint_and_building(building_data: dict) -> tuple:
    reversed_dict = {value: key for key, value in building_data.items()}
    levels_indexes = sorted(reversed_dict.keys(), key=lambda x: (x < 0, abs(x)))
    level_index = levels_indexes[0]
    layer = QgsProject.instance().mapLayersByName(reversed_dict[level_index])[0]
    footprint = generate_footprint(layer)
    building = IMDF.Building(footprint)
    return footprint, building


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

sheets_dict = {}


for sheet_n in wks.worksheets():
    sheet = sheet_n.get_all_values()
    sheets_dict[sheet_n.title] = sheet



exporting_handler = ExportingHandler(IMDF_PATH)



# 0 - Creating Address object
address = IMDF.Address(exporting_handler.address_str,
                       exporting_handler.locality_str,
                       exporting_handler.province_str,
                       exporting_handler.country_str,
                       exporting_handler.postal_code)
# 1 - Venue +
# If there are more then 1 building there should venue layer exist in this project and venue polygon should occupies all buildings

try:
    layer_venue = QgsProject.instance().mapLayersByName('venue')[0]
except:
    int('There are no venue layer in this project. It should exist because there are more than 1 building')
layer_venue = processing.run("native:reprojectlayer", {'INPUT': layer_venue, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']

feature_venue = list(layer_venue.getFeatures())[0]
venue = IMDF.Venue(feature_venue, category=exporting_handler.category_venue, name=exporting_handler.name_venue)
venue.assign_address_id(address.uid)
# 2 - Footprint +
# Subterranean


exporting_handler = ExportingHandler(IMDF_PATH)

exporting_handler.break_table_into_settings_structure(sheets_dict)
exporting_handler.set_address(address)
exporting_handler.set_venue(venue)



for building_name, building_data  in exporting_handler.building_dct.items():


    footprint, building = create_footprint_and_building(building_data)



    building.assign_address_id(address.uid)


    exporting_handler.add_footprint(footprint)
    exporting_handler.add_building(building)

    for level_name, level_index in building_data.items():
        layer_level_input = QgsProject.instance().mapLayersByName(level_name)[0]
        # branching for several buildings
        if len(exporting_handler.building_dct) > 1:
            layer_level_input.selectByExpression(f"\"building\" = '{building_name}'")
            reference_layer = processing.run("native:saveselectedfeatures", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})
            reference_layer = reference_layer['OUTPUT']
        else:
            reference_layer = layer_level_input

        # Level
        layer_level = processing.run("native:fixgeometries", { 'INPUT' : reference_layer, 'OUTPUT' : 'TEMPORARY_OUTPUT' })['OUTPUT']
        # layer_level = processing.run("native:buffer", {'DISSOLVE': True, 'DISTANCE': 0.02, 'END_CAP_STYLE': 0, 'INPUT': layer_level, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
        # layer_level = processing.run("native:buffer",{'DISSOLVE': True, 'DISTANCE': -0.02, 'END_CAP_STYLE': 0, 'INPUT': layer_level,'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})['OUTPUT']
        layer_level = processing.run("native:dissolve", { 'FIELD' : [], 'INPUT' :  layer_level, 'OUTPUT' : 'TEMPORARY_OUTPUT', 'SEPARATE_DISJOINT' : False })['OUTPUT']
        layer_level = processing.run("native:deleteholes", {'INPUT': layer_level, 'MIN_AREA': 0.0, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})['OUTPUT']
        layer_level = processing.run("native:fixgeometries", {'INPUT': layer_level, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
        layer_level_4326 = processing.run("native:reprojectlayer", {'INPUT': layer_level, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
        feature = list(layer_level_4326['OUTPUT'].getFeatures())[0]

        level = IMDF.Level(feature, level_name, building, address, ordinal=level_index)



        # Features
        layer_level_input = processing.run("native:fixgeometries", {'INPUT': reference_layer, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']
        layer_level_input = processing.run("native:multiparttosingleparts", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT' })['OUTPUT']

        # # Test
        # layer_level_input = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': -0.001, 'END_CAP_STYLE': 1,
        #                                                      'INPUT': layer_level_input, 'JOIN_STYLE': 1,
        #                                                      'MITER_LIMIT': 2,
        #                                                      'OUTPUT': 'memory:', 'SEGMENTS': 5})['OUTPUT']

        # layer_level_input = processing.run("native:snapgeometries", {'BEHAVIOR': 0,
        #                                                              'INPUT': layer_level_input,
        #                                                              'OUTPUT': 'TEMPORARY_OUTPUT',
        #                                                              'REFERENCE_LAYER': layer_level,
        #                                                              'TOLERANCE': 0.0015})['OUTPUT']
        # layer_level_input = processing.run("native:snapgeometries", {'BEHAVIOR': 0,
        #                                                              'INPUT': layer_level_input,
        #                                                              'OUTPUT': 'TEMPORARY_OUTPUT',
        #                                                              'REFERENCE_LAYER': layer_level_input,
        #                                                              'TOLERANCE': 0.00075})['OUTPUT']


        layer_level_input = processing.run("native:reprojectlayer", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']
        layer_level_input = processing.run("native:removenullgeometries", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})['OUTPUT']




        exporting_handler.add_level(level)
        process_features(list(layer_level_input.getFeatures()), level, exporting_handler)



        # Working with openings:
        if QgsProject.instance().mapLayersByName(f'{level_name}_openings') != []:
            openings_layer = QgsProject.instance().mapLayersByName(f'{level_name}_openings') [0]
            openings_layer = prepare_layer_for_processing(openings_layer, layer_level_input)



            exporting_handler.process_openings(openings_layer, level)
        else:
            print('Exporting of "openings" layer is failed')

        # Working with amenities points:
        if QgsProject.instance().mapLayersByName(f'{level_name}_amenities') != []:
            amenities_points_layer = QgsProject.instance().mapLayersByName(f'{level_name}_amenities')[0]
            amenities_points_layer = processing.run("native:reprojectlayer", {'INPUT': amenities_points_layer, 'OUTPUT': 'TEMPORARY_OUTPUT',
                                                             'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})['OUTPUT']
            for amenity in amenities_points_layer.getFeatures():

                unit_geojson = get_unit(exporting_handler.units, amenity, level.uid)
                # print('unit_geojson', unit_geojson)
                unit = IMDF.Unit(create_qgs_feature_from_imdf_feature(unit_geojson),
                                 unit_geojson['properties']["level_id"],
                                 unit_geojson['properties']["category"])

                amenity = create_amenity(amenity.attribute('tid'), unit, exporting_handler,
                                         name=amenity.attribute('name'), centroid=eval(amenity.geometry().asJson()))
                if amenity:
                    exporting_handler.add_amenity(amenity)

        else:
            print('Exporting of "openings" layer is failed')





exporting_handler.dump_files()