"""
	a collection of basic tools for dealing with version management on shotgun	
		
	implemented methods:
	
		* connect() - creates a connection to the SG server, MUST be run before calling any other method
		
			returns [SHOTGUN OBJECT]
			
			
		* get_project(project_id[INT]) - 'helper' function used by other methods - grabs the project shortcode for a given project id (used to name versions and media)
		
			project_id [INT]: must be a valid SG project id (normally this method would only be called from other methods where the project id is already given)
			
			returns [DICT]: an SG project entity including field data for the project short code for the given project (eg 'STU', 'OSR')
			
		
		* get_user(data[DICT]) - 'helper' function used by other methods - simple wrapper around sg.find_one() that grabs user metadata
		
			data MUST consist of two key/value pairs that can uniquely describe a valid HumanUser entity in SG
			'field': [STRING] the name of the uniquely valued field used to generate the query (in practice it must be one of: 'id', 'name', 'login' or 'email' though this method is provided to generally get an id from a more commonly known value like the user name)
			'value': [INT/STRING] the actual data used to generate the query (eg 37, 'stu', 'Stu Aitken', 'stuart.aitken@axisanimation.com')
			
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
		
"""

__author__ = 'Stu Aitken <stuartaitken@axisanimation.com>'
__maintainer__ = 'Stu Aitken <stuartaitken@axisanimation.com>'
__status__  = 'Prototype'
__version__ = '0.85'
__date__    = '05-05-2013'
__copyright__ = 'Copyright 2013, Axis Animation'
__contributors__ = ('Roman Ignatov <romanignatov@axisanimation.com>')

#common imports
import sys
import os
import subprocess
from pprint import pprint


# pythonista specific imports
ipad = False
try:
	import console
	if console:
		sys.path.append('..')
		from sg_api3 import Shotgun
		ipad = True

except:
	# normal imports
	from shotgun import Shotgun

# import server settings
import AX_sg_setup
	

def connect():

	SERVER_PATH = 'https://%s.shotgunstudio.com' %AX_sg_setup.STUDIO
	SCRIPT_USER = 'AX_SGversionTools' 
	SCRIPT_KEY = AX_sg_setup.KEY
	sg = Shotgun(SERVER_PATH, SCRIPT_USER, SCRIPT_KEY)
	return sg
		
def get_user(data):

	fields = ['id', 'code', 'name']
	filters = [[data['field'], 'is', data['value']]]
	user = sg.find_one("HumanUser", filters, fields)
	return user

def get_project(project_id):
	fields = ['sg_projcode', 'id', 'code', 'name']
	filters = [['id', 'is', project_id]]
	project = sg.find_one("Project", filters, fields)
	return project
	
def get_entity(data):
	
	fields = ['id', 'code', 'project']

	# get project
	filters = [['code', 'is', data['project_code']]]
	project = sg.find_one("Project", filters, fields)
	if not project:
		raise ShotgunMatchError('Project %s not found on server' %data['project_code'])
	
	# get parent
	if data['entity_type'] == 'Shot':
		filters = [
    		['project', 'is', {'type':'Project', 'id':project['id']}],
    		['code', 'is', data['parent_code']]
   		 	]
		parent = sg.find_one('Sequence', filters,fields)
		if not parent:
			raise ShotgunMatchError('Sequence %s not found on server' %data['parent_code'])

	# get entity
	
	filters = [
	    ['project', 'is', {'type':'Project', 'id':project['id']}],    
	   	['code', 'is', data['entity_code']]
	   	]
	if data['entity_type'] == 'Shot':
		filters.append(['sg_sequence', 'is', {'type':'Sequence', 'id':parent['id']}])
		fields.append('sg_sequence')
	elif data['entity_type'] == 'Asset':
		filters.append(['sg_asset_type', 'is', data['parent_code']])
		fields.append('sg_asset_type')
    	
	entity = sg.find_one(data['entity_type'], filters, fields)
	if not entity:
		raise ShotgunMatchError('%s %s not found on server'%(data['entity_type'], data['entity_code']))
	return entity
	
	
def get_all_versions(entity, *args):

	fields = ['id', 'code', 'entity', 'user', 'description', 'sg_increment', 'sg_version_type', 'project']
	filters = [['entity','is',{'type':entity['type'],'id':entity['id']}]]
	
	if args:
		if 'type' in args[0]:
			filters.append(['sg_version_type', 'is', args[0]['type']])
			
	versions = sg.find("Version",filters,fields)
	return versions

def get_latest_version(entity, data):

	versions = get_all_versions(entity, data)
	
	if len(versions) > 0:
		inc = 0
		i = 0
		result = 0
		for version in versions:
			if version['sg_increment'] > inc:
				inc = int(version['sg_increment'])
				result = i
			i=i+1
		return versions[result]
	else:
		return {}
		
def get_specific_version(entity, data):

	versions = get_all_versions(entity, data)
	
	if len(versions) > 0:
		for version in versions:
			if int(version['sg_increment']) == int(data['inc']):
				return version
	else:
		return {}
			
	
def create_version(entity, data):
	
	if entity['type'] == 'Shot':
		parent_code = entity['sg_sequence']['name']
	elif entity['type'] == 'Asset':
		parent_code = entity['sg_asset_type']
	else:
		raise ShotgunMatchError('%s is not a shot or asset' %entity['code'])
		
	current = get_latest_version(entity, data)
	if current:
		inc = int(current['sg_increment']) + 1
	else:
		inc = 1
		
	project = get_project(entity['project']['id'])
	if not project:
		raise ShotgunMatchError('Project %s not found on server' %entity['project']['code'])
	
	code = "%s_%s_%s_%s_%s" %(project['sg_projcode'], parent_code, entity['code'], data['type'], str(inc).zfill(3))
	
	user = get_user(data['user'])
	if not user:
		raise ShotgunMatchError('User %s not found on server' %data['user']['value'])
	
	new_data = {
    'project': {'type':'Project','id':entity['project']['id']},
    'code': code,
    'description': data['note'],
    'entity': {'type':entity['type'],'id':entity['id']},
	'sg_version_type':data['type'],
	'sg_increment': inc,
    'user': {'type':'HumanUser','id':user['id']},
    'sg_first_frame': data['in'],
    'sg_last_frame': data['out'],
    'frame_count': int(data['out']) - int(data['in']) + 1,
    }
	
	version = sg.create("Version", new_data)
	return version
	

def get_version_path(entity, version):

	#get related data not passed directly via arguments
	
	if os.name == 'nt':
		root = 'X:'
	else:
		root = '/Volumes/output'
	
	project = get_project(entity['project']['id'])
	if not project:
		raise ShotgunMatchError('Project %s not found on server' %entity['project']['code'])
	
	parent = ''	
	if entity['type'] == 'Shot':
		parent = entity['sg_sequence']['name']
	elif entity['type'] == 'Asset':
		parent = entity['sg_asset_type']
	else:
		raise ShotgunMatchError('%s is not a shot or asset' %entity['code'])
	
	#set default schema map - order of list generates order of components in filepath
	map = [
		root,
		project['code'] + '_' + project['name'],
		'output',
		entity['type'],
		parent,
		entity['code'],
		version['sg_version_type'],
		str(version['sg_increment']).zfill(3),
		]
	
	#if any particular combination of entity & version type needs a custom map, override the default here
	
	#set paths
	base_path = ""
	for token in map:
		base_path = base_path + token + "/"
	media_path = base_path + 'preview/' + version['code']
	frame_path = base_path + 'frames/' + version['code']
	paths = {
		'in': os.path.normpath(frame_path + '_%04d.exr'),
		'out': os.path.normpath(media_path + '.mov'),
		'mp4': os.path.normpath(media_path + '_SG.mp4'),
		'webm': os.path.normpath(media_path + '_SG.webm'),
		}
	
	return paths

def create_version_media(paths, data):
	
	#avoid pythonista trying to call ffmpeg :)
	if not ipad:
	
		ffmpeg = os.path.normpath('M:/applications/utilties/ffmpeg/bin/ffmpeg.exe') 
		rate = ' -r %s ' %data['fps']
		
		#create prores master
		vcodec = ' -pix_fmt yuv422p10le -vcodec prores -profile:v 3 -vendor ap10 -filter:v scale="1280:trunc(ow/a/2)*2"'
		acodec = ' -acodec pcm_s16le -ar 48k'
		commandline = ffmpeg + rate + '-i ' + paths['in'] + vcodec + acodec + rate + paths['out']
		subprocess.call(commandline)
		
		#create mp4 for SG
		vcodec = ' -pix_fmt yuv420p -vcodec libx264 -filter:v scale="1280:trunc(ow/a/2)*2" -b:v 4000k -vprofile high -bf 0 -strict experimental'
		acodec = ' -acodec aac -ab 160k -ac 2'
		commandline = ffmpeg + rate + '-i ' + paths['in'] + vcodec + acodec + rate + paths['mp4']
		subprocess.call(commandline)
		
		#create webm for SG
		vcodec = ' -pix_fmt yuv420p -vcodec libvpx -filter:v scale="1280:trunc(ow/a/2)*2" -b:v 4000k -quality realtime -cpu-used 0 -qmin 10 -qmax 42'
		acodec = ' -acodec libvorbis -aq 60 -ac 2'
		commandline = ffmpeg + rate + '-i ' + paths['in'] + vcodec + acodec + rate + paths['webm']
		subprocess.call(commandline)
		
	return get_media_status(paths)

def get_frame_status(paths, data):
	
	i = data['in']
	status = True
	while i <= data['out']:
		if not os.path.exists(paths['in'][:-8] + str(i).zfill(4) + '.exr'):
			status = False
		i = i + 1
			
	return status

def get_media_status(paths):
			
	status = {}
	for key, value in paths.iteritems():
		if key != 'in':
			if os.path.exists(value):
				status.update({key: True})
			else:
				status.update({key: False})
	
	return status


def update_version_media(paths, version):
	
	url_root = 'http://yogi.axis.rocks'
	
	local_link = {
		'local_path': paths['out'],
		'name': version['code'] + '.mov',
		'content_type': 'video/quicktime',
		'link_type': 'local',
		}
		
	mp4_link = {
		'url': url_root + paths['mp4'][2:].replace('\\','/'),
		'name': version['code'] + '_SG.mp4',
		'content_type': 'video/mp4',
		'link_type': 'web',
		}
		
	webm_link = {
		'url': url_root + paths['webm'][2:].replace('\\','/'),
		'name': version['code'] + '_SG.webm',
		'content_type': 'video/webm',
		'link_type': 'web',
		}
	
	data = {
		'sg_path_to_frames': paths['in'].replace('%04d',str(version['sg_first_frame']).zfill(4)),
		'sg_path_to_movie': paths['out'],
		'sg_uploaded_movie_mp4': mp4_link,
		'sg_uploaded_movie_webm': webm_link,
		'sg_uploaded_movie_transcoding_status': 1,
		#'sg_uploaded_movie_frame_rate': version['fps'],
		'sg_status_list': 'rev',
		}
		
	if not ipad:
		data.update({'sg_qt': local_link})
		
	updated = sg.update("Version", version['id'], data)
	return updated

	
# run tests if run as script

if __name__ == '__main__':
	
	# pythonista specific console commands
	if ipad:
		console.clear()
		console.show_activity()
	
	# test data:
	
	entity_data = {
		'project_code': 'S0001',
		'entity_type': 'Shot',
		'entity_code': 'sh010',
		'parent_code': 'sc01',
		}
		
	user_data = {
		'field':'name',
		'value':'Stu Aitken',
		}
	
	version_data = {
		'type': 'Lighting',
		'inc': 1,
		'user': user_data,
		'note': 'this version added via SGVersionTools %s' %__version__,
		'in': 1,
		'out': 65,
		'fps': 30,
		}
	
	# create server link
	print "\ncreating connection to SHOTGUN...\n"
	sg = connect()
	
	# match given entity details
	print "finding entity \n"
	entity = get_entity(entity_data) 
	print 'found matching entity:\n'
	pprint (entity)
	print ""
		
	# find all versions
	print 'finding all versions...\n'
	result = get_all_versions(entity)
	if not result:
		print "no versions found.\n"
	else:
		print "found %s version(s)" %len(result)
		for version in result:
			print "\n"
			pprint (version)
		print ""

	# find all versions matching specified type
	print 'finding all %s versions...\n' %version_data['type']
	result = get_all_versions(entity, version_data)
	if not result:
		print "no %s versions found. \n" %version_data['type']
	else:
		print "found %s %s version(s):\n" %(len(result), version_data['type'])
		for version in result:
			pprint (version)	
			print ""
			
	# find latest version
	print 'finding latest %s version...\n' %version_data['type']
	latest_version = get_latest_version(entity, version_data)
	if not latest_version:
		print "no %s versions found.\n" %version_data['type']
	else:
		pprint (latest_version)
		print ""
		
	# find specific version
	print "finding version:\n"
	specific_version = get_specific_version(entity, version_data)
	if not specific_version:
		print "version not found.\n"
	else:
		pprint (specific_version)
		print ""
		
	# create a new version
	print "creating new version: \n"
	new_version = create_version(entity, version_data)	
	pprint (new_version)
	print ""
		
	# get media paths for new version
	print "looking up version media paths: \n"
	path = get_version_path(entity, new_version)
	pprint (path)
	print ""
	
	# check frames completed
	print "checking frames exist...\n"
	status = get_frame_status(path, version_data)
	pprint (status)
	print ""
		
	# create media
	print "creating version media: \n"
	status = create_version_media(path, version_data)
	pprint (status)
	print ""
		
	# update version with media links
	print "updating version with links to media: \n"
	updated = update_version_media(path, new_version)
	pprint (updated)
	print ""
		
	sg.close()
