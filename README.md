#Converts your QGIS indoor project to IMDF
## Structure
 - IMDF.py - file with classes
 - IMDF_script.py - script to run in QGIS (Alt + P)
 - config_`project_name`.txt - includes all other configuration variables for current project where `project_name` is name of QGIS project what you want to export
 - *.json - file with your google service account credentials
## Before running*
Please set up this variables inside config_`project_name`.txt (`project_name` is current QGIS project name variable):
 - We **should** specify variables for [address](https://register.apple.com/resources/imdf/Address/ "Address Apple Specification") layer:

| Variable       |  Explanation                |
|----------------|------------------|
| address_str    | Formatted postal address, excluding suite/unit identifier   |
| locality_str   | Official locality (e.g. city, town) component of the postal address |
| province_str   | Province (e.g. state, territory) component of the postal address        |
| country_str    | Country component of the postal address        |
| postal_code    | Mail sorting code extension associated with the postal code - it Could be None        |
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
- We **should** create the [venue](https://register.apple.com/resources/imdf/Venue/) layer in the existing QGIS project. We **MUST** create venue layer by hand if there are several buildings in one QGIS project. In the venue **should** be only one polygon. Name of the layer - 'venue'
- If project consist of several building than the `building` field in level layers SHOULD be filled for every feature

Please set up this variables inside `IMDF_script.py`. We **should** specify:
 - `IMDF_PATH` - path to IMDF.py, 
 - `CREDENTIALS_PATH` - path to Service Account Credentials json file

Others 
 - [Footprint](https://register.apple.com/resources/imdf/Footprint/) level can include polygons with categories: 'Subterranean', 'Ground', 'Aerial'. In the script we are creating only 'Ground' category temporary polygon based on ground floor
 - [Openings](https://register.apple.com/resources/imdf/Opening/) - required to properly show entrances to the units. You need to create openings manually and name each layer by adding '_openings'. For example '1F_openings'. `f'{level_name}_openings'`. We don't need to create openings for 'Kiosk', 'Section', 'Fixture'
 - [Optional] [Section](https://register.apple.com/resources/imdf/types/section) - is an area that serves a specific purpose. For example, an airport would have baggage claim, check-in area, gate and security sections. Field `section_category` need to be created in the data and filled with one of the possible values based on [Apple sections list](https://register.apple.com/resources/imdf/reference/categories#section:~:text=restricted-,Section,-Category)
 - [Optional] [Kiosk](https://register.apple.com/resources/imdf/types/kiosk) - can be placed on top of the unit. Algorithm will create an occupant feature if `occupant` (filled with typeCode of retail/service related value what can be applicable for occupant for example 'cafes-coffee-tea-houses') and `occupant_tid` (filled with tid what can be applicable for occupant for example '20600') are filled with values
 - [Optional] [Fixtures](https://register.apple.com/resources/imdf/types/fixtures) - having this features required for some types of buildings for example [airports](https://register.apple.com/resources/imdf/apple/airport#:~:text=The%20following%20feature%2Dtypes/categories%20MUST%20be%20captured%3A)
 - [Optional] [Amenities as a separate points layer](https://register.apple.com/resources/imdf/types/amenities) - we can have amenities in a points layer that can be added to the final file. To use name each points layer with amenities by adding '_amenities'. For example '1F_amenities'. `f'{level_name}_amenities'`

 - For correct forming we need to fill `tid` column for all objects in level layers according to our [taxonomy](https://docs.google.com/spreadsheets/d/1gPPFUw2a1L9Gd1IcVnGJXTPA_fiAMM6ez2kg1A_zj8U/edit#gid=1810304683 'Taxonomy V2')
 - For correct forming we need to place all names/titles of the objects in `name` column in level layers
  ## Run
 If all set, run the `IMDF_script.py` inside your QGIS. The *.geojson parts of IMDF should be created
  
