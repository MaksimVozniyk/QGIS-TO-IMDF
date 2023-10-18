#TODO:
# 1. Change PATH variable to save IMDF project files inside .../project/IMDF path
# 2. Set branch for export several building in one project set building_dct variable
# 3. Separate address variables, building_dict to config_`project_name`.txt
# Line 116 The Ground Floor should be taken from building_dct variable with 0 ordinal!
# -----------------------------------------------------------------------------------------------------------------------
# Setting up path to IMDF.py folder
IMDF_PATH = 'H:/My Drive/Mapping/Common/Pointr Qgis/scripts/IMDF'
# Setting up path to folder to save outfiles (IMDF format)
PATH = 'H:/My Drive/Mapping/Common/Pointr Qgis/scripts/IMDF/Gatwick'
# Setting up full path to Service Account Credentials json file
CREDENTIALS_PATH = 'C:/Users/OON/Dropbox/TaxonomySpreedSheet-f9ebbf3ef5f8.json'

PROJECT_NAME = QgsProject.instance().fileInfo().baseName()
 
with open(f'{IMDF_PATH}/config_{PROJECT_NAME}.txt','r') as file:
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
import sys
from importlib import reload
import gspread
import processing
from oauth2client.service_account import ServiceAccountCredentials

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
occupant_rows = {}
amenity_rows = {}
sheets_dict = {}

for sheet_n in wks.worksheets():
    sheet = sheet_n.get_all_values()
    sheets_dict[sheet_n.title] = sheet
for index_in_sheet, row in enumerate(sheets_dict['Apple Unit Categories'], 1):
    if 59 > index_in_sheet > 1:
        unit_rows[row[0]] = [x.strip() for x in row[1].split(',')]
    if 77 < index_in_sheet < 138:
        occupant_rows[row[0]] = [x.strip() for x in row[1].split(',')]
    if 149 < index_in_sheet < 303:
        amenity_rows[row[0]] = [x.strip() for x in row[1].split(',')]


# 0 - Creating Address object
address = IMDF.Address(address_str, locality_str, province_str, country_str, postal_code)
# 1 - Venue +
# If there are more then 1 building there should venue layer exist in this project and venue polygon should occupies all buildings
if len(building_dct) == 1:
    if QgsProject.instance().mapLayersByName('venue') == []:  # If the venue layer doesn't exist it would be created from GF
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
for b in building_dct.keys():
    for l in building_dct[b].keys():
        # Searching ordinal 0 in building levels to create a footprint for each building
        if building_dct[b][l] == 0:
            layer_gf = QgsProject.instance().mapLayersByName('L00')[0]
            # branching for several buildings
            if len(building_dct) > 1:
                layer_gf.selectByExpression(f"\"building\" = '{b}'")
                reference_layer = processing.run("native:saveselectedfeatures",
                                                 {'INPUT': layer_gf, 'OUTPUT': 'TEMPORARY_OUTPUT'})
                reference_layer = reference_layer['OUTPUT']
            else:
                reference_layer = layer_gf
            layer_gf = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': 1e-06, 'END_CAP_STYLE': 0, 'INPUT': reference_layer, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})
            layer_gf = processing.run("native:fixgeometries", { 'INPUT' : layer_gf['OUTPUT'], 'OUTPUT' : 'TEMPORARY_OUTPUT' })
            layer_gf = layer_gf['OUTPUT']
            _layer_gf = processing.run("native:dissolve", {'FIELD': [], 'INPUT': layer_gf, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})
            footprint_layer = processing.run("native:deleteholes", {'INPUT': _layer_gf['OUTPUT'], 'MIN_AREA': 0.1, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})
            footprint_layer = processing.run("native:reprojectlayer", {'INPUT': footprint_layer['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
            feature_footprint = list(footprint_layer['OUTPUT'].getFeatures())[0]
            footprint = IMDF.Footprint(feature_footprint)
            # 3 Building
            building = IMDF.Building(footprint)

    footprints["features"].append(footprint.as_dict(False))
    buildings["features"].append(building.as_dict(False))

    for level_name in building_dct[b].keys():
        layer_level_input = QgsProject.instance().mapLayersByName(level_name)[0]
        # branching for several buildings
        if len(building_dct) > 1:
            layer_level_input.selectByExpression(f"\"building\" = '{b}'")
            reference_layer = processing.run("native:saveselectedfeatures", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})
            reference_layer = reference_layer['OUTPUT']
        else:
            reference_layer = layer_level_input

        layer_level_input = processing.run("native:buffer", {'DISSOLVE': False, 'DISTANCE': 1e-06, 'END_CAP_STYLE': 0, 'INPUT': reference_layer, 'JOIN_STYLE': 0, 'MITER_LIMIT': 2, 'OUTPUT': 'TEMPORARY_OUTPUT', 'SEGMENTS': 5})
        layer_level_input = processing.run("native:fixgeometries", { 'INPUT' : layer_level_input['OUTPUT'], 'OUTPUT' : 'TEMPORARY_OUTPUT' })
        layer_level_input = layer_level_input['OUTPUT']
        layer_level = processing.run("native:dissolve", {'FIELD': [], 'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})
        layer_level = processing.run("native:deleteholes", {'INPUT': layer_level['OUTPUT'], 'MIN_AREA': 0.1, 'OUTPUT': 'TEMPORARY_OUTPUT', 'CRS': 4326})
        layer_level = processing.run("native:reprojectlayer", {'INPUT': layer_level['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
        feature = list(layer_level['OUTPUT'].getFeatures())[0]
        ordinal = building_dct[b][level_name]
        level = IMDF.Level(feature, level_name, building, address, ordinal=ordinal)
        levels["features"].append(level.as_dict(False))

        layer_level_input = reference_layer
        layer_level = processing.run( "native:multiparttosingleparts", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT' })
        layer_level = processing.run( "native:reprojectlayer", {'INPUT': layer_level['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
        layer_level_input = layer_level['OUTPUT']

        for key in unit_rows.keys():

            # selecting units in layer_level
            if unit_rows[key] != ['all other']:
                lst_tid = [x[:-2]+f'{i:02d}' for x in unit_rows[key] for i in range(20)]

                # Temp solution only for Macys North
                if '111300' in lst_tid:
                    lst_tid.append('30505')

                strs = '\',\''.join(lst_tid)
                strs = f'"TID" IN (\'{strs}\')'

            else:
                existing_tid = [xx for x in unit_rows.values() for xx in x  if xx not in ['-','all other']]
                existing_tid = [x[:-2]+f'{i:02d}' for x in existing_tid for i in range(20)]

                # Temp solution only for Macys North
                existing_tid.append('30505')

                strs = '\',\''.join(existing_tid)
                strs = f'"TID" NOT IN (\'{strs}\')'

            layer_level_input.selectByExpression(strs)
            selected = processing.run("native:saveselectedfeatures", {'INPUT': layer_level_input, 'OUTPUT': 'TEMPORARY_OUTPUT'})
            selected = processing.run("native:removenullgeometries", {'INPUT': selected['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT'})
            selected = processing.run("native:reprojectlayer", {'INPUT': selected['OUTPUT'], 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
            print(len(list(selected['OUTPUT'].getFeatures())), key)
            for feature in list(selected['OUTPUT'].getFeatures()):
                unit = IMDF.Unit(feature, level, key)
                units["features"].append(unit.as_dict(False))

                # Creating Anchors for rooms, Creating Occupant for Anchors
                if key == 'room':
                    anchor = IMDF.Anchor(feature, unit, address)
                    anchors["features"].append(anchor.as_dict(False))

                    cat_oc = None
                    for key_oc in occupant_rows.keys():
                        form_occupant_compleate_tid_list_for_key = [x[:-2]+f'{i:02d}' for x in occupant_rows[key_oc] for i in range(20)]
                        if str(feature.attribute('TID')) in form_occupant_compleate_tid_list_for_key:
                            cat_oc = key_oc
                    occupant = IMDF.Occupant(feature, anchor, cat_oc)
                    occupants["features"].append(occupant.as_dict(False))

                # Creating amenities
                cat_am = None
                for key_am in amenity_rows.keys():
                    form_amenity_compleate_tid_list_for_key = [x[:-2]+f'{i:02d}' for x in amenity_rows[key_am] for i in range(20)]
                    if str(feature.attribute('TID')) in form_amenity_compleate_tid_list_for_key:
                        cat_am = key_am
                if cat_am:
                    print(cat_am)
                    amenity = IMDF.Amenity(unit, cat_am, address)
                    amenities["features"].append(amenity.as_dict(False))

            layer_level_input.removeSelection()

        # Working with openings:
        if QgsProject.instance().mapLayersByName('openings') != []:
            openings_layer = QgsProject.instance().mapLayersByName('openings') [0]
            if openings_layer.crs().authid() != 'EPSG:4326':
                op = processing.run("native:reprojectlayer", {'INPUT' : openings_layer, 'OUTPUT': 'TEMPORARY_OUTPUT', 'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:4326')})
                openings_layer = op['OUTPUT']

            for feature_opening in openings_layer.getFeatures():
                opening = IMDF.Opening(feature_opening, level)
                openings["features"].append(opening.as_dict(False))
        else:
            print('Exporting of "openings" layer is failed')


# Aerial


# 4  Level + Unit + Anchor + Amenity + Occupant + Openings

#Checking if PATH exists
if os.path.exists(PATH) is False:
    os.makedirs(PATH)
    
# SAVING
address.toFile(f'{PATH}/address.geojson')
venue.toFile(f'{PATH}/venue.geojson')

with open(f'{PATH}/footprint.geojson', 'w') as outfile:
    json.dump(footprints, outfile, indent=4)
    
with open(f'{PATH}/building.geojson', 'w') as outfile:
    json.dump(buildings, outfile, indent=4)

with open(f'{PATH}/level.geojson', 'w') as outfile:
    json.dump(levels, outfile, indent=4)

with open(f'{PATH}/unit.geojson', 'w') as outfile:
    json.dump(units, outfile, indent=4)

with open(f'{PATH}/anchor.geojson', 'w') as outfile:
    json.dump(anchors, outfile, indent=4)

with open(f'{PATH}/occupant.geojson', 'w') as outfile:
    json.dump(occupants, outfile, indent=4)

with open(f'{PATH}/amenity.geojson', 'w') as outfile:
    json.dump(amenities, outfile, indent=4)

if openings["features"] != []:
    with open(f'{PATH}/opening.geojson', 'w') as outfile:
        json.dump(openings, outfile, indent=4)

