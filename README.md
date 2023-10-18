#Converts your QGIS indoor project to IMDF
## Structure
 - IMDF.py - file with classes
 - IMDF_script.py - script to run in QGIS (Alt + P)
 - config_`project_name`.txt - includes all other configuration variables for current project where `project_name` is name of QGIS project what you want to export
 - *.json - file with your google service account credentials
## Before running
Please set up this variables inside config_`project_name`.txt (`project_name` is current QGIS project name variable):
 - We **should** specify variables for [address](https://register.apple.com/resources/imdf/Address/ "Address Apple Specification") layer:

| Variable       |  Explanation                |
| ------------- |------------------|
| address_str    | Formatted postal address, excluding suite/unit identifier   |
| locality_str     | Official locality (e.g. city, town) component of the postal address |
| province_str  | Province (e.g. state, territory) component of the postal address        |
| country_str  | Country component of the postal address        |
| postal_code  | Mail sorting code extension associated with the postal code - it Could be None        |
*In the future I hope we will find a solution to get correct address automatically*

 - We **should** set up the [`category_venue`](https://register.apple.com/resources/imdf/Categories/#venue 'Find needed category for the building'), `name_venue` variable for each specific project
 - We **MUST** form a dictonary `building_dct` where keys should be building names and values should be `level_lst` type variables. `level_lst` - dictionary where `keys` should be a level names and a `values` (-int type) should be [ordinal](https://register.apple.com/resources/imdf/Level/ "Level") - which tell the position of the layer in levels pie, where the 0 is base-ground level:
 ```
level_lst_1 = {'Basement_floor': -1, 'GF': 0, 'L2': 1 , 'L3': 2}
level_lst_2 = {'Basement_floor': -1, 'GF': 0, 'L2': 1 , 'L3': 2, 'L4': 3}
```
```
building_dct = {'Building_name_1': level_lst_1,
                'Building_name_2': level_lst_2,
                ...}
```  
```
Real example:
building_dct = {'Building_name_1': {'Basement_floor': -1, 'GF': 0, 'L2': 1 , 'L3': 2},
                'Building_name_2': {'Basement_floor': -1, 'GF': 0, 'L2': 1 , 'L3': 2, 'L4': 3}}

```
- We **should** create the [venue](https://register.apple.com/resources/imdf/Venue/) layer in the existing QGIS project, otherwise venue would be created from GF temporarily. We **MUST** create venue layer by hand if there are several buildings in one QGIS project. In the venue **should** be only one polygon
- If project consist of several building than the `building` field in level layers SHOULD be filled for every feature

Please set up this variables inside `IMDF_script.py`
 - We **should** specify `IMDF_PATH` - path to IMDF.py, `CREDENTIALS_PATH` - path to Service Account Credentials json file


 - The [footprint](https://register.apple.com/resources/imdf/Footprint/) level can include polygons with categories: 'Subterranean', 'Ground', 'Aerial'. In the script we creating only 'Ground' category temporary polygon based on ground floor
 - [Openings](https://register.apple.com/resources/imdf/Opening/) - is a support layer to show entrances. We don't have algorithm to extract this layer from level, but in generally it can be created from border of walkways and facilities/retails/socials objects or it can be created by hand if needed. Type - line.

![opening](https://user-images.githubusercontent.com/35077349/75184909-1549c880-573d-11ea-996c-0da952e3153c.png)
 - For correct forming we need to fill `TID` column for all objects in level layers according to our [taxonomy](https://docs.google.com/spreadsheets/d/1gPPFUw2a1L9Gd1IcVnGJXTPA_fiAMM6ez2kg1A_zj8U/edit#gid=1810304683 'Taxonomy V2')
 - For correct forming we need to place all names/titles of the objects in `Name` column in level layers
  ## Run
 If all set, run the `IMDF_script.py` inside your QGIS. The *.geojson parts of IMDF should be created!!!
  
