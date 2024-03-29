#this script is for running all functions
#preprocess script should be run first
import os
import json
import rasterio
from rasterio.mask import mask
import pandas
import geopandas as gpd
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']


def process_regional_hazard(country, region, haz_scene):
    """
    This function creates a regional hazard .tif

    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    #prefered GID level
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    # for region in region_dict:
    for scene in haz_scene:

        #now we write out at the regional level
        filename_out = scene.format("shp")
        folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #loading in hazard .shp
        filename = scene.format("shp") 
        path_hazard = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', 'national', filename)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = gpd.read_file(path_hazard, crs="EPSG:4326")
        gdf_hazard_int = gpd.overlay(gdf_hazard, gdf_region, how='intersection')
        if len(gdf_hazard_int) == 0:
            continue
        os.makedirs(path_out)
        gdf_hazard_int.to_file(path_out, crs='epsg:4326')

    return

def process_regional_population(country, region, haz_scene):
    """
    This function creates a regional population .shp
    
    """
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    # for region in region_dict:
    for scene in haz_scene:

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join('data', 'processed', iso3 , 'population', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        filename_haz = scene.format("shp") # if the region doesn't have a hazard skip it
        folder_haz = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_haz = os.path.join(folder_haz, filename_haz)
        if not os.path.exists(path_haz):
            continue

        #loading in national population file
        filename = 'ppp_2020_1km_Aggregated.shp' #each regional file is named using the gid id
        folder= os.path.join('data', 'processed', iso3 , 'population', 'national')
        path_pop = os.path.join(folder, filename)
        gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")
        
        #prefered GID level
        filename = "gadm36_{}.shp".format(gid_region)
        path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
        gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
        gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    
        gdf_pop = gpd.overlay(gdf_pop, gdf_region, how='intersection')
        if len(gdf_pop) == 0:
            continue
        os.makedirs(path_out)
        gdf_pop.to_file(path_out, crs='epsg:4326')

    return

def process_regional_rwi(country, region):
    """
    creates relative wealth estimates .shp file by region

    """
    iso3 = country['iso3']                 
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    #loading in gid level shape file
    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    for region in region_dict:

        filename = '{}.shp'.format(gid_id)
        folder_out = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions' )
        path_out = os.path.join(folder_out, filename)

        if os.path.exists(path_out):
            continue

        #loading in rwi info
        filename = '{}_relative_wealth_index.shp'.format(iso3) #each regional file is named using the gid id
        folder= os.path.join(BASE_PATH, 'processed', iso3 , 'rwi', 'national')
        path_rwi= os.path.join(folder, filename)
        if not os.path.exists(path_rwi):
            continue
        gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")

        gdf_rwi_int = gpd.overlay(gdf_rwi, gdf_region, how='intersection')
        if len(gdf_rwi_int) == 0:
            continue
        os.makedirs(path_out)   

        gdf_rwi_int.to_file(path_out, crs="EPSG:4326")

    return


def intersect_hazard_pop(country, region, haz_scene):
    """
    This function creates an intersect between the 
    coastal flood hazard area and population.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    # for region in region_dict:
    for scene in haz_scene:

        # now we write out path at the regional level
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #load in population by region .shp file
        filename_pop = '{}'.format(gid_id) #each regional file is named using the gid id
        path_pop = os.path.join(BASE_PATH, 'processed', iso3 , 'population', scene, filename_pop)
        if not os.path.exists(path_pop):
            continue
        gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")

        #load in hazard .shp file
        filename_out = scene.format("shp")
        folder_out = os.path.join('data', 'processed', iso3 , 'hazards', 'inuncoast', gid_id)
        path_hazard = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_hazard):
            continue
        gdf_hazard = gpd.read_file(path_hazard, crs="EPSG:4326")
    
        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop', scene)
        path_out = os.path.join(folder_out, filename_out)
        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected = gpd.overlay(gdf_pop, gdf_hazard, how='intersection')
        if len(gdf_affected) == 0:
            continue

        gdf_affected = gdf_affected.to_crs('epsg:3857')

        # area to 1 km
        gdf_affected['area_km2'] = gdf_affected['geometry'].area / 1e6
        gdf_affected['pop_est'] = gdf_affected['value_1']* gdf_affected['area_km2']
    
        gdf_affected = gdf_affected.to_crs('epsg:4326')

        if not os.path.exists(path_out):
            os.makedirs(path_out)
        gdf_affected.to_file(path_out, crs='epsg:4326')

    return

#intersect vulnerable population and rwi
def intersect_rwi_pop(country, region, haz_scene):
    """
    This function creates an intersect between the 
    relative wealth index and vulnerable population.
    
    """
    #assigning variables
    iso3 = country['iso3']
    gid_region = country['gid_region']
    gid_level = 'GID_{}'.format(gid_region)
    gid_id = region[gid_level]

    filename = "gadm36_{}.shp".format(gid_region)
    path_region = os.path.join('data', 'processed', iso3,'gid_region', filename)
    gdf_region = gpd.read_file(path_region, crs="EPSG:4326")
    gdf_region = gdf_region[gdf_region[gid_level] == gid_id]
    region_dict = gdf_region.to_dict('records')

    # for region in region_dict:
    for scene in haz_scene:

        filename_out = '{}'.format(gid_id) #each regional file is named using the gid id
        folder_out = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'rwi_pop_hazard', scene)
        path_out = os.path.join(folder_out, filename_out)

        if os.path.exists(path_out):
            continue

        #load in hazard .shp file
        filename = '{}.shp'.format(gid_id)
        path_rwi = os.path.join(BASE_PATH, 'processed', iso3, 'rwi', 'regions', filename )
        if not os.path.exists(path_rwi):
            continue
        gdf_rwi = gpd.read_file(path_rwi, crs="EPSG:4326")
        gdf_rwi = gdf_rwi.to_crs('epsg:3857')
        
        filename = '{}'.format(gid_id) #each regional file is named using the gid id
        path_pop= os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'hazard_pop', scene, filename)
        if not os.path.exists(path_pop):
            continue
        gdf_pop =  gpd.read_file(path_pop, crs="EPSG:4326")
        gdf_pop = gdf_pop.to_crs('epsg:3857')

        os.makedirs(path_out)
        gdf_pop_rwi = gpd.overlay(gdf_rwi, gdf_pop, how='intersection')
        if len(gdf_pop_rwi) == 0:
            continue
        gdf_pop_rwi = gdf_pop_rwi.rename(columns = {'value_1':'population'})
        gdf_pop_rwi=gdf_pop_rwi.rename(columns = {'value_2':'flood_depth'})
        gdf_pop_rwi.to_file(path_out, crs='epsg:4326')

    return


if __name__ == "__main__":

    haz_scene = [
        "inuncoast_historical_wtsub_2080_rp0100_0.{}", 
        "inuncoast_historical_wtsub_2080_rp1000_0.{}", 
        "inuncoast_rcp4p5_wtsub_2080_rp0100_0.{}", 
        "inuncoast_rcp4p5_wtsub_2080_rp1000_0.{}", 
        "inuncoast_rcp8p5_wtsub_2080_rp0100_0.{}", 
        "inuncoast_rcp8p5_wtsub_2080_rp1000_0.{}"
        ]
    
    path = os.path.join('data', 'countries.csv')
    countries = pandas.read_csv(path, encoding='latin-1')
    countries = countries.to_dict('records')

    for country in countries:

        if country['Exclude'] == 1:
            continue
        if country['income_group'] == 'HIC':
            continue

        iso3 = country['iso3']
        gid_region = country['gid_region']
        gid_level = 'GID_{}'.format(gid_region)

        #coastal look up load in
        filename = 'coastal_lookup.csv'
        folder = os.path.join(BASE_PATH, 'processed', iso3, 'coastal')
        path_coast= os.path.join(folder, filename)
        if not os.path.exists(path_coast):
            continue
        coastal = pandas.read_csv(path_coast)
        coast_list = coastal['gid_id'].values.tolist()

        #set the filename depending our preferred regional level
        filename = "gadm36_{}.shp".format(gid_region)
        folder = os.path.join('data','processed', iso3, 'gid_region')
        
        #then load in our regions as a geodataframe
        path_regions = os.path.join(folder, filename)
        regions = gpd.read_file(path_regions, crs='epsg:4326')#[:2]
        region_dict = regions.to_dict('records')

        print("--Processing iso3: {}".format(iso3))

        for region in region_dict:
            gid_id = region[gid_level]

            if not region[gid_level] in coast_list:
                continue

            # ##skip regions that have already been fully processed
            # filename_int= '{}'.format(gid_id) #each regional file is named using the gid id
            # folder_int = os.path.join(BASE_PATH, 'processed', iso3 , 'intersect', 'rwi_pop_hazard')
            # path_int= os.path.join(folder_int, filename_int)
            # if os.path.exists(path_int):
            #     continue

            print("---- working on {}".format(region[gid_level]))

            print("-working on process_regional_hazard")
            process_regional_hazard(country, region, haz_scene)

            print("working on process_regional_population")
            process_regional_population(country, region, haz_scene)

            print("-working on process_regional_rwi")
            process_regional_rwi(country, region)

            print("-working on intersect_hazard_pop")
            intersect_hazard_pop(country, region, haz_scene)

            print("-working on intersect_rwi_pop")
            intersect_rwi_pop(country, region, haz_scene)
