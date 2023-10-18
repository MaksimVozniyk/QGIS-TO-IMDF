import uuid
import json

class Venue:
    def __init__(self, feature, category=None, name=None):
        self.uid = str(uuid.uuid4())
        self.geometry = eval(feature.geometry().asJson())
        self.centroid = eval(feature.geometry().centroid().asJson())
        self.address = None  # Connection to address feature ID
        self.buildings = []  # Linked building ID s
        self.restriction = None  # feature.attribute("restriction")

        if category:
            self.category = category
        else:
            self.category = feature.attribute("category")

        if name:
            self.name = {"en": f"{name}"}
        else:
            self.name = eval(feature.attribute("name"))

    def assignBuilding(self, uid):
        self.buildings.append(uid)

    def assignAddressID(self, uid):
        self.address = uid

    def as_dict(self, verbose):
        dict = {
            "name": "venue",
            "type": "FeatureCollection",
            "features": [
                {
                    "id": self.uid,
                    "type": "Feature",
                    "feature_type": "venue",
                    "geometry": self.geometry,
                    "properties":
                    {
                        "category": self.category,
                        "restriction": self.restriction,
                        "name": self.name,
                        "alt_name": None,
                        "hours": None,
                        "website": None,
                        "phone": None,
                        "display_point": self.centroid,
                        "address_id": self.address,

                    }
                }
            ]
        }

        if(verbose):
            print(json.dumps(dict))
        return dict

    def toFile(self, path):
        dict = self.as_dict(False)
        with open(path, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

class Footprint:
    def __init__(self, feature):
        self.uid = str(uuid.uuid4())
        self.geometry = eval(feature.geometry().asJson())
        self.centroid = eval(feature.geometry().centroid().asJson())
        self.name = None
        self.category = 'ground'
        self.buildings = []

    def assignBuilding(self, id):
        self.buildings.append(id)

    def as_dict(self, verbose):
        footprint = {
            "id": self.uid,
            "type": "Feature",
            "feature_type": "footprint",
            "geometry": self.geometry,
            "properties": {
                "category": self.category,
                "name": self.name,
                "building_ids": self.buildings
            }
        }
        if(verbose):
            print(json.dumps(footprint, sort_keys=False, indent=4))
        return footprint


class Building:
    def __init__(self, footprint):
        self.uid = str(uuid.uuid4())
        footprint.assignBuilding(self.uid)
        #venue.assignBuilding(self.uid)
        self.name = footprint.name
        self.centroid = footprint.centroid

    def as_dict(self, verbose):
        building = {
            "id": self.uid,
            "type": "Feature",
            "feature_type": "building",
            "properties":
            {
                "category": "unspecified",
                "restriction": None,
                "name": self.name,
                "alt_name": None,
                "display_point": self.centroid,
                "address_id": None,
            },
            "geometry": None}
        if(verbose):
            print(json.dumps(building, sort_keys=False, indent=4))
            print("\n")
        return building

class Level:
    def __init__(self, feature, level_name, building, address, ordinal=None): # We can specify level order relative to others levels

        self.uid = str(uuid.uuid4())
        self.name = level_name
        self.ordinal = ordinal
        self.geometry = eval(feature.geometry().asJson())
        self.centroid = eval(feature.geometry().centroid().asJson())
        self.building_id = building.uid

        if ordinal is None:
            if self.name.lower() in ['-2', 'b2']:
                self.ordinal = -2
            if self.name.lower() in ['lg', '-1', 'lower', 'lower_floor', 'lower_level', 'basement', 'b1']:
                self.ordinal = -1
            if self.name.lower() in ['gf', '0', 'ground', 'ground_floor', 'ground_level']:
                self.ordinal = 0
            if self.name.lower() in ['l1', '1', 'level 1', 'level_1']:
                self.ordinal = 1
            if self.name.lower() in ['l2', '2', 'level 2', 'level_2']:
                self.ordinal = 2 # Should be 2
            if self.name.lower() in ['l3', '3', 'level 3', 'level_3']:
                self.ordinal = 3
        else:
            print('We need to specify level ')
        self.address_uid = address.uid

    def as_dict(self, verbose):
        level = {
            "id": self.uid,
            "type": "Feature",
            "feature_type": "level",
            "geometry": self.geometry,
            "properties": {
                "category": "unspecified",
                "restriction": None,
                "ordinal": self.ordinal,
                "outdoor": False,
                "name":
                {"en": self.name},
                "short_name":
                {"en": self.name},
                "display_point": self.centroid,
                "address_id": self.address_uid,
                "building_ids": [self.building_id]
            }
        }
        if(verbose):
            print(json.dumps(level, sort_keys=False, indent=4))
            print("\n")
        return level

class Unit:
    def __init__(self, feature, level, category):

        self.uid = str(uuid.uuid4())
        self.geometry = eval(feature.geometry().asJson())
        self.centroid = eval(feature.geometry().pointOnSurface().asJson())
        self.category = category
        self.level = level.uid
        if str(feature.attribute('name')) == 'NULL':
            self.name = None
        else:
            self.name = {"en": feature.attribute('name')}

    def as_dict(self, verbose):
        unit = {
            "id": self.uid,
            "type": "Feature",
            "feature_type": "unit",
            "geometry": self.geometry,
            "properties": {
                "category": self.category,
                "restriction": None,
                "accessibility": None,
                "name": self.name,
                "alt_name": None,
                "display_point": self.centroid,
                "level_id": self.level
            }
        }
        if(verbose):
            print(json.dumps(unit, sort_keys=False, indent=4))
            print("\n")
        return unit

class Address:
    def __init__(self, address_str, locality_str, province_str, country_str, postal_code):
        self.uid = str(uuid.uuid4())
        self.address = address_str
        self.unit = None
        self.locality = locality_str
        self.province = province_str
        self.country = country_str
        self.postal_code = postal_code

    def as_dict(self, verbose):
        address = {
            "name": "address",
            "type": "FeatureCollection",
            "features": [{
            "id": self.uid,
            "type": "Feature",
            "feature_type": "address",
            "geometry": None,
            "properties": {
                "address": self.address,
                "unit": self.unit,
                "locality": self.locality,
                "province": self.province,
                "country": self.country,
                "postal_code": self.postal_code,
                "postal_code_ext": None
                            }
                        }]
                }
        if(verbose):
            print(json.dumps(address, sort_keys=False, indent=4))
            print("\n")
        return address

    def toFile(self, path):
        dict = self.as_dict(False)
        with open(path, 'w') as outfile:
            json.dump(dict, outfile, indent=4)

class Anchor:
    def __init__(self, feature, unit, address):

        self.uid = str(uuid.uuid4())
        self.unit_uid = unit.uid
        self.centroid = eval(feature.geometry().pointOnSurface().asJson())
        self.address_id = address.uid

    def as_dict(self, verbose):
        anchor = {
             "id": self.uid,
              "type": "Feature",
             "feature_type": "anchor",
              "geometry": self.centroid,
              "properties": {
                    "address_id": self.address_id,
                    "unit_id": self.unit_uid
                            }
                }
        if(verbose):
            print(json.dumps(anchor, sort_keys=False, indent=4))
            print("\n")
        return anchor

class Occupant:
    def __init__(self, feature, anchor, category):
        self.uid = str(uuid.uuid4())
        self.category = category
        self.anchor_id = anchor.uid
        if str(feature.attribute('name')) == 'NULL':
            self.name = {"en": category}
        else:
            self.name = {"en": feature.attribute('name')}

    def as_dict(self, verbose):
        occupant = {
              "id": self.uid,
              "type": "Feature",
              "feature_type": "occupant",
              "geometry": None,
              "properties": {
                "category": self.category ,
                "name": self.name,
                "phone": None,
                "website": None,
                "hours": None,
                "validity" : None,
                "anchor_id": self.anchor_id,
                "correlation_id": None
              }
            }
        if(verbose):
            print(json.dumps(occupant, sort_keys=False, indent=4))
        return occupant

class Amenity:
    def __init__(self, unit, category, address):
        self.uid = str(uuid.uuid4())
        self.category = category
        self.unit_uid = unit.uid
        self.centroid = unit.centroid
        self.address = address.uid

        print(unit.name, str(unit.name).lower(), type(unit.name))
        if str(unit.name).lower() == 'none':
            self.name = None
        else:
            self.name = {"en": unit.name}

    def as_dict(self, verbose):
        amenity = {
                      "id": self.uid,
                      "type": "Feature",
                      "feature_type": "amenity",
                      "geometry": self.centroid,
                      "properties": {
                        "category": self.category,
                        "accessibility": None,
                        "name": self.name,
                        "alt_name": None,
                        "phone": None,
                        "website": None,
                        "hours": None,
                        "unit_ids": [self.unit_uid],
                        "address_id": self.address,
                        "correlation_id": None
                      }
                    }
        if(verbose):
            print(json.dumps(amenity, sort_keys=False, indent=4))
        return amenity

class Opening:
    def __init__(self, feature, level):
        self.uid = str(uuid.uuid4())
        self.geometry = eval(feature.geometry().asJson())
        self.level_id = level.uid

    def as_dict(self, verbose):
        opening = {
                  "id": self.uid,
                  "type": "Feature",
                  "feature_type": "opening",
                  "geometry": self.geometry,
                  "properties": {
                    "category": "pedestrian",
                    "accessibility": None,
                    "access_control": None,
                    "door": None,
                    "name": None,
                    "alt_name": None,
                    "display_point": None,
                    "level_id": self.level_id
                  }
                }
        if(verbose):
            print(json.dumps(opening, sort_keys=False, indent=4))
        return opening