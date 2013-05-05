AX_SGversionTools
=================

**Prototype wrapper for dealing with studio shotgun commits**

###Reference: implemented methods:

The module consists of three main types of function:

* simple helpers designed to simplify certain queries, mainly used internally, but exposed in case they may be useful

* wrappers around sg.find() and sg.find_one() designed to easily query for Shots, Assets and related Versions with relevant identifying information that is likely to be easily ascertained from the context of being called from within a specific maya scene or fusion comp (ie where things like SG entity ids will not be evident)

* more specific tools to carry out various media related tasks such as mapping paths to and creating media for the SG review pipeline


The library is designed to be as application and task agnostic as possible in order to simplify development and allow easy maintainability  - any necessary parts (eg hooks into existing tool-sets perhaps) that require context specific code should be kept in separate files to allow a degree of 'sandboxing', but should also follow a consistent API in terms of how they interface with the core shared functionality. 

In particular I've tried to design the shotgun specific functionality and processes to be as generically applicable as possible (eg it should be as valid for someone modelling a character in modo as it is for someone comping VFX tests in fusion, providing the necessary application specific processes have been implemented)

I suspect with some clever thinking more of the entire versioning pipeline can be unified and shared than might at first be obvious (eg even things like certain UIs could be shared as long as the applications support python. Underlying specific functions - eg play blasting vs rendering on the farm can be abstracted away from core publishing features)


	
**connect()**

creates initial connection to the SG server, MUST be run before calling any other method

**returns:**

`dict` *Shotgun Object*

___

			
**get_project(** `int` *project_id* **)**

Very simple wrapper around sg.find_one() to return project metadata
		
`int` *project_id*
must be a valid SG project id or an exception will be raised

>**Returns:**
			
`dict` *Project*
an SG project entity containing various field data including the project short code (eg 'STU', 'OSR')
		

___

		
**get_user(** `dict` *data* **)**

'helper' function used by other methods - simple wrapper around sg.find_one() that grabs user metadata
		
`dict` *data*
must consist of two key/value pairs that uniquely describe a valid HumanUser entity in SG:

* `string` *field*
the name of the uniquely valued field used to generate the query (in practice it must be one of: 'id', 'name', 'login' or 'email')

* `string` *value*
the field value data used to generate the query (eg 28, 'mike', 'Mike Smith', 'mike@somewhere.com')
			
**Returns:**   

`dict` *HumanUser*
an SG HumanUser entity containing field data (crucially id)

___
			
**get_entity(** `dict` *data* **)**

a simple wrapper for sg.find_one() to grab entity metadata for a defined shot or asset

`dict` *data*
must consist of 4 keys that can together, uniquely describe a valid Shot or Asset entity within the SG schema: 

* `string` *entity_type*
>> must be either 'Shot' or 'Asset'

* `string` *entity_code*
>> the name of the shot or asset (eg 'sh010', 'MyAsset')
 		
* `string` *parent_code*
>> the name of the shot or asset's parent container (eg 'sc01', 'character')

>> note that **Shot** parent containers are currently defined in SG as links to a separate entity class (Scenes or Sequences) whereas **Asset** parent containers are more simply defined as a field value restricted to a limited set of strings. 

>>this difference is however abstracted away inside any methods that have to make this distinction in terms of how they interact with Shotgun - the interface for either type is identical

* `string` *project_code*
>> the project code identifier (eg 'A0875', 'S0001')

**Returns:**

`dict` *Shot* - or - `dict` *Asset*
an Sg entity consisting of various fields on the requested entity

note that for any returned fields that link to other entities values will contain nested dicts themselves describing those linked entities 
	

**get_all_versions(** `dict` *entity* , `dict` *data* **)**	

> finds all versions associated with the supplied entity
		
> `dict` *entity*
> should be a single SG entity query result - ie as returned from get_entity()

> `dict` *data*
> is optional and if supplied needs to describe a version type and contain just one key:

* `string` *type*
> an identifier for the task context (eg 'Lighting', 'Model') - this should match one of the list options for 'type' from the associated SG field
			
>**Returns:**

> `list` *Versions*
> a list of `dicts` describing sg version entities associated with the supplied shot/asset entity (further limited to version type if supplied) - empty list if none found
			


**get_latest_version(** `dict` *entity* , `dict` *data* **)**	

> a wrapper for get_all_versions() that grabs the latest version only
		
> arguments are the same as get_all_versions() with the exception that data is REQUIRED
		
> `dict` *entity*
> should be a single SG entity query result - ie as returned from get_entity()

> `dict` *data*
> needs to describe a version type and contain just one key:

* `string` *type*
> an identifier for the task context (eg 'Lighting', 'Model') - this should match one of the list options for 'type' from the associated SG field
			
>**Returns:**

> `dict` *Version*
> the latest (as ordered by the 'inc' field) SG version entity of the specified type, associated with the supplied shot/asset entity - empty list if none found

			
**get_specific_version(** `dict` *entity* , `dict` *data* **)**

> a wrapper for get_all_versions() that grabs a specific version only - should be used only for returning a version that currently already exists or to check if it does so.
 
> arguments are the same as get_all_versions() with the exception that data is REQUIRED and it must also contain an additional key identifying the version increment to be returned as well as one identifying type
 
> `dict` *entity*
> should be a single SG entity query result - ie as returned from get_entity()
 
> `dict` *data*
>  needs to describe a version type **and** increment and contain two keys: 

 * `string` *type*
> an identifier for the task context (eg 'Lighting', 'Model') - this should match one of the list options for 'type' from the associated SG field

 * `int` *inc*
> the version increment to be returned (eg: 1, 5, etc)
 
>**Returns:** 
 
> `dict` *Version*
> the specified (ie by type and increment) SG version entity associated with the supplied shot/asset entity -  or an empty Dict if no matches were found (can thus be used to check if a specific version exists)
	
			
		
**create_version(** `dict` *entity* , `dict` *data* **)** 

> creates a new version, incrementing the previous version number for the specific version type by 1 (If there is one) - it calls get_latest_version() first in order to do this

> `dict` *entity*
> an SG entity object for a valid shot or asset as returned by get_entity()

> `dict` *data*
>  needs to describe various properties of the new version as follows:

>**Returns:** 

> `dict` *Version*
> the newly created SG version entity -  raises an exception if this is not returned by shotgun

		
			
**get_version_path(** `dict` *entity* , `dict` *version* **)** 

> used to generate appropriate file paths to version media - essentially maps the shotgun schema to the file system.
	
> `dict` *entity*
> an SG entity object for a valid shot or asset as returned by get_entity()

> `dict` *version*
> an SG version object for a valid existing version as returned by create_version() or any of the get_version methods that return a single version
			
>**returns:**

> `dict` *path*
> contains 4 keys describing valid system filepaths to the input and output media used by shotgun:

* `string` *input*
> a path to where the version frames on disk ought to be located

* `string` *mov*
> a path to the primary quicktime compiled version media

* `string` *mp4*
> A path to a secondary more highly compressed mp4 version media (used by shotguns web player)

* `string` *webm*
> A path to a secondary more highly compressed webm version media (used by shotguns web player for browsers that don't support mp4)


		
**create_version_media(** `dict` *paths* **)** 

> a wrapper around ffmpeg used to create version media from an existing input source (ie a playblast avi or comped frames)
		
> `dict` *paths*
>  as returned by get_version_path() - the two methods are explicitly designed to be chained together. needs to contain 4 keys:

* `string` *input*
> a path to where the version frames on disk ought to be located
		
* `string` *mov*
> a path to the primary quicktime compiled version media

* `string` *mp4*
> A path to a secondary more highly compressed mp4 version media (used by shotguns web player)
 
* `string` *webm*
> A path to a secondary more highly compressed webm version media (used by shotguns web player for browsers that don't support mp4)

>**returns:**

> `dict` *status*
> contains 3 keys denoting the success or otherwise of the media creation - one for each compiled output:

			
			
**update_version_media(** `dict` *version* , `dict` *paths* **)** 

> adds version media paths to the version entity in SG - splitting this into a separate function allows for asynchronous processing of the various steps involved, though normally this would be called directly after create_version_media()
		
> `dict` *version*
> an SG version entity as returned by get_entity()

> `dict` *paths*
> a collection of filepaths as returned by get_version_media()
 
* `string` *input*
> a path to where the version frames on disk ought to be located

* `string` *mov*
> a path to the primary quicktime compiled version media

* `string` *mp4*
> a path to a secondary more highly compressed mp4 version media (used by shotguns web player)

* `string` *webm*
> A path to a secondary more highly compressed webm version media (used by shotguns web player for browsers that don't support mp4)
			
> **Returns: **

> `dict` *Version*
> an updated SG version object with updated field values 
	
			
