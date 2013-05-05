AX_SGversionTools
=================

Prototype wrapper for dealing with studio shotgun commits


implemented methods:
	
* connect() - creates a connection to the SG server, MUST be run before calling any other method
		
returns [SHOTGUN OBJECT]
			
			
* get_project(project_id[INT]) - 'helper' function used by other methods - grabs the project shortcode for a given project id (used to name versions and media)
		
project_id [INT]: must be a valid SG project id (normally this method would only be called from other methods where the project id is already given)
			
returns [DICT]: an SG project entity including field data for the project short code for the given project (eg 'STU', 'OSR')
			
		
* get_user(data[DICT]) - 'helper' function used by other methods - simple wrapper around sg.find_one() that grabs user metadata
		
data MUST consist of two key/value pairs that can uniquely describe a valid HumanUser entity in SG
'field': [STRING] the name of the uniquely valued field used to generate the query (in practice it must be one of: 'id', 'name', 'login' or 'email' though this method is provided to generally get an id from a more commonly known value like the user name)
'value': [INT/STRING] the actual data used to generate the query (eg 28, 'mike', 'Mike Smith', 'mike@somewhere.com')
			
returns [DICT]: an SG HumanUser entity containing relevant details on the user (crucially id)
			
		
* get_entity(data[DICT]) - a simple wrapper for sg.find_one() to grab entity metadata for a defined shot or asset
		
data MUST define a SHOT or ASSET and contain valid values for the following keys:
'project_code': [STRING] must be the projects code identifier as this is the only thing guaranteed to be unique outside the id (eg 'A0875', 'S0001')
'entity_type': [STRING] must be either 'Shot' or 'Asset'
'entity_code': [STRING] the name of the shot or asset(eg 'sh010', 'MyAsset')
'parent_code': [STRING] the name of the shot or asset's parent container (eg 'sc01',	'character')
			
note that shot parent containers are currently defined in SG as links to a separate entity class (scenes or sequences) whereas Asset parent containers are more simply defined as a field value restricted to a limited set of strings
this difference is however abstracted away inside any methods that have to make this distinction in terms of how they interact with Shotgun - the interface for either type is identical

returns [DICT] (SG entity): an Sg entity consisting of various key/value pairs for various fields of the entity as returned by the standard SG api - most importantly it returns the entity id's
note that for any returned fields that link to other entities values will contain nested dicts themselves describing those linked entities 
			
			
* get_all_versions(entity[DICT], (data[DICT])) - finds all versions associated with supplied entity
		
entity should be a single SG entity query result - ie as returned from get_entity()
data is optional and if supplied needs describe a version type and contain just one key:
'type': [STRING](eg 'Lighting', 'Model')
			
returns [LIST]: list of [DICT]s describing sg version entities on the supplied shot/asset entity (further limited to version type if supplied) - empty list if none found
			
			
* get_latest_version(entity[DICT], data[DICT]) - a wrapper for get_all_version() that grabs the latest version only
		
arguments are the same as get_all_versions() with the one exception that data is REQUIRED and needs to contain a valid value for the following key
'type': [STRING] (eg 'Lighting', 'Model')
		
returns [DICT]: a single SG version entity describing the lastest (ie highest inc) version for the supplied entity and version type
			
		
* get_specific_version(entity[DICT], data[DICT]) - another wrapper for get_all_versions() that grabs a specific version identified by both type and inc 		
		
arguments are the same as get_all_versions() with the exception that data is REQUIRED, and needs to describe the requested version with valid values for TWO keys
'type' [STRING}: (eg 'Lighting', 'Model')
'inc': [INT] (eg 1)		

returns [DICT]: a single version entity representing the specific version identified		
			
		
* create_version(entity, data) - creates a new version, adding to any existing version increments
		
			
* get_version_path(entity[DICT], version[DICT]) - method to create file paths to version media (maps SG schema to filesystem paths)
		
entity: an SG entity object for a valid shot or asset as returned by get_entity()
version: an SG version object for a valid version (ie make sure its created first!) as returned by any of the get_version methods that return a single version
			
returns [DICT]: contains two key value pairs:
'in' [STRING]: a path to where the version frames on disk ought to be located
'out' [STRING]: a path to the compiled version media (ie mov) which will not yet be created
			
		
* create_version_media(path[DICT]) - a wrapper around ffmpeg used to create version media from existing media
		
path needs to contain two key/value pairs as is returned by get_version_path() - ie the two methods are explicitly designed to be chained together 
'in' [STRING]: a path to where the version frames on disk ought to be located - if there is an alternative input (eg maya playblast on local drive) then this value should be updated before calling
'out' [STRING]: a path to the compiled version media (ie mov) which will not yet be created 
			
returns [DICT]: a revised path dict also now containing mp4 and webm paths in addition to the original in and out
'in' [STRING]: a path to where the version frames on disk ought to be located
'out' [STRING]: a path to the compiled version media (ie mov) which will not yet be created 
'mp4' [STRING]: a path to the compiled mp4 media
'webm' [STRING]: a path to the compiled webm media
			
			
* update_version_media(version[DICT], paths[DICT]) - automates adding version media paths to version entity in SG
		
version [DICT]: an SG version entity as returned by get_entity()
paths [DICT]: a collection of filepaths as returned by create_version_media()
			
returns [DICT]: a new version object with updated field values 
