"""
a class wrapper around the shotgun api for dealing with version management

"""

__author__ = 'Stu Aitken <stuartaitken@axisanimation.com>'
__maintainer__ = 'Stu Aitken <stuartaitken@axisanimation.com>'
__status__  = 'Prototype'
__version__ = '0.96'
__date__    = '09-05-2013'
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
	
SERVER_PATH = 'https://axis.shotgunstudio.com'
SCRIPT_USER = 'AX_SGversionTools' 
SCRIPT_KEY = 'f8b3d11c5b1af7177b55324869f6ecb8d3c768b0'

class sg_version():
	
	def __init__ (self, context = {}):
		
		self._project = {}
		self._sequence = {}
		self._entity = {}
		self._schema = ''
		self._parent = ''
		self._media_paths = {}
		self._os_root = ''
		self._echo_state = True
		
		self._sg = Shotgun(SERVER_PATH, SCRIPT_USER, SCRIPT_KEY)
		if context:
			self.set_context(context)
	
	def set_context(self, context):
		
		examples = (
		['Shot','project','sequence','shot','version_type'],
		['Asset','project','asset_type','asset','version_type'],
		['Scene','project','sequence','version_type'],
		)
		
		self._project = {}
		self._sequence = {}
		self._entity = {}
		self._schema = ''
		self._parent = ''
		self._media_paths = {}
		self._os_root = ''
		
		if not len(context) in range(4,6):
			self._echo("not enough arguments to set context - examples:", examples)
			return {}
		
		#set project
		fields = ['id','code','name','sg_projcode']
		filters = [['code', 'is', context[1]]]
		self._project = self._sg.find_one('Project', filters, fields)
		if self._project:
			self._echo("Project sucessfully set to:", self._project)
		else:
			self._echo("Project %s not found. Project not set" %context[1])
			return {}
		
		if context[0] is 'Shot' or 'shot':
			
			self._schema = 'Shot'
			
			# set sequence
			fields = ['id','code','type']
			filters = [['project', 'is', self._project],['code', 'is', context[2]]]	
			self._sequence = self._sg.find_one('Sequence', filters, fields)		
			if not self._sequence:
				self._echo("Scene %s not found. Shot not set" %context[2])
				return {}
				
			#set shot
			fields = ['id','code','type','sg_sequence']
			filters = [
				['project', 'is', self._project],
				['sg_sequence', 'is', self._sequence],
				['code','is', context[3]]
				]
			self._entity = self._sg.find_one('Shot', filters, fields)
			if self._entity:
				self._echo("Shot sucessfully set to:", self._entity)
				self._parent = context[2]
				self._version_type = context[4]
			else:
				self._echo("Shot %s not found in Scene %s. Shot not set" %(context[3],context[2]))
				return {}
				
		elif context[0] is 'Asset' or 'asset':
			
			self._schema = 'Asset'
			
			#set asset
			fields = ['id','code','type','sg_asset_type']
			filters = [
				['project', 'is', self._project],
				['sg_asset_type', 'is', context[2]],
				['code','is', context[3]]
				]
			self._entity = self._sg.find_one('Asset', filters, fields)
			if self._entity:
				self._echo("Asset sucessfully set to:", self._entity)
				self._parent = context[2]
				self._version_type = context[4]
			else:
				self._echo("Asset %s of type %s not found. Asset not set" %(context[3],context[2]))
				return {}
				
		elif context[0] is 'Scene' or 'scene' or 'Sequence' or 'sequence':
			
			self._schema = 'Scene'
			
			# set sequence
			fields = ['id','code','type']
			filters = [
				['project', 'is', self._project],
				['code', 'is', context[2]]
				]	
			self._entity = self._sg.find_one('Sequence', filters, fields)		
			if self._sequence:
				self._echo("Scene sucessfully set to:", self._sequence)
				self._version_type = context[3]
			else:
				self._echo("Scene %s not found. Scene not set" %context[2])
				return {}
					
		else:
			self._echo("entity type set incorrectly. Context not set")
			return {}
			
		return {
			'project': self._project,
			'entity': self._entity,
			'version': self._version_type,
			}
		
	
	def _version_setup(self):
		
		fields = [
			'id',
			'code', 
			'sg_version_type', 
			'sg_increment',
			'sg_first_frame',
			'sg_last_frame',
			'frame_count',
			'sg_uploaded_movie_frame_rate',
			'description',
			'entity',
			'user',
			'project',
			]

		filters = [
			['entity', 'is', self._entity],
			['sg_version_type', 'is', self._version_type],
			]
		
		return filters, fields
		
	def find_all(self):
	
		if not self._schema:
			self._echo("Context not properly set. No Versions found")
			return {}

		filters, fields = self._version_setup()	
		versions = self._sg.find("Version", filters, fields)
			
		if versions:
			self._echo("%s %s Versions exist: " %(len(versions), self._version_type))
			return versions
		else:
			self._echo("No %s versions exist" %self._version_type)
			return {}
	
	def find_one(self, inc):
	
		if not self._schema:
			self._echo("Context not properly set. No Versions found")
			return {}

		filters, fields = self._version_setup()
		filters.append(['sg_increment', 'is', inc])
		version = self._sg.find_one("Version", filters, fields)
		
		if version:
			self._echo("version v%s exists: %s" %(str(inc).zfill(3), version['code']))
			return version
		else:
			self._echo("%s version v%s not found" %(self._version_type, str(inc).zfill(3)))
			return {}

			
	def find_last(self):
	
		if not self._schema:
			self._echo("Context not properly set. No Versions found")
			return {}

		filters, fields = self._version_setup()			
		sum_fields = [{'field':'sg_increment', 'type':'maximum'}]		
		summary = self._sg.summarize('Version', filters, sum_fields)
		if not summary['summaries']['sg_increment']:
			self._echo("no versions found") 
			return {}	
		filters.append(['sg_increment', 'is', summary['summaries']['sg_increment']])
		version = self._sg.find_one('Version', filters, fields)
			
		if version:
			self._echo("latest %s version found is: v%s" %(self._version_type, str(version['sg_increment']).zfill(3)))
			return version
		else:
			self._echo("No %s versions found" %self._version_type)
				
	def create_version(self, v_data = {}):
			
		if not self._schema:
			self._echo("Context not properly set. No Versions found")
			return {}	
		
		last_version = self.find_last()
		if last_version:	
			inc = last_version['sg_increment'] + 1
		else:
			inc = 1
		
		schema = [self._project['sg_projcode']]
		
		if self._parent:
			schema.append(self._parent)
		
		schema.append(self._entity['code']) 
		schema.append(self._version_type)
		schema.append(str(inc).zfill(3))
			
		code = ''
		for s in schema:
			code = code + s + '_'
		code = code[:-1]
		
		new_data = {
			'project': self._project,
			'code': code,
			'entity': self._entity,
			'sg_version_type': self._version_type,
			'sg_increment': inc,
			'sg_status_list': 'sub'
			}
		
		artist = {}
		if 'user' in v_data:
			artist = self._set_user(v_data['user'])
		if artist:
			new_data.update({'user': artist})
		if 'fps' in v_data:
			new_data.update({'sg_uploaded_movie_frame_rate': float(v_data['fps'])})	
		v_keys = ['in','out','note']
		n_keys = ['sg_first_frame','sg_last_frame','description']
		for i in range(len(v_keys)):
			if v_keys[i] in v_data:
				new_data.update({n_keys[i]: v_data[v_keys[i]]})
		if 'in' and 'out' in v_data:
			new_data.update({'frame_count': int(v_data['out']) - int(v_data['in']) + 1})
			
		new_version = self._sg.create("Version", new_data)
			
		if new_version:
			self._echo("new %s version created: %s" %(new_version['sg_version_type'], new_version['code']))
			return new_version
		else:
			self._echo("Unknown shotgun error. New Version could not be created")
	
	
	def create_media(self, version, input_path = ''):
				
		#get project data
		fields = ['id','code','name','sg_projcode']
		filters = [['id', 'is', version['project']['id']]]
		project = self._sg.find_one('Project', filters, fields)
	
		#set schema map - order of list generates order of components in filepath
		map = [
			project['code'] + '_' + project['name'],
			'output',
			version['entity']['type'] + 's',
			]
		
		# get project parent sequence		
		if version['entity']['type'] == 'Shot':
			fields = ['id','code','sg_sequence']
			filters = [['id', 'is', version['entity']['id']]]
			entity = self._sg.find_one('Shot', filters, fields)
			map.append(entity['sg_sequence']['name'])
		
		#get asset parent type
		elif version['entity']['type'] == 'Asset':
			fields = ['id','code','sg_asset_type']
			filters = [['id', 'is', version['entity']['id']]]
			entity = self._sg.find_one('Asset', filters, fields)
			map.append(entity['sg_asset_type'])
		
		# finish schema		
		map.append(version['entity']['name'])
		map.append(version['sg_version_type'])
		map.append(str(version['sg_increment']).zfill(3))
		
		#set paths
		base_path = ""
		for m in map:
			base_path = base_path + m + os.sep
		media_path = base_path + 'preview' + os.sep + version['code']
		frame_path = base_path + 'frames' + os.sep + version['code']
			
		if os.name == 'nt':
			self._os_root = 'X:' + os.sep
		else:
			self._os_root =  os.sep + 'Output' + os.sep
		
		self._media_paths = {
			'input': os.path.normpath(frame_path + '_%04d.exr'),
			'mov': os.path.normpath(media_path + '.mov'),
			'mp4': os.path.normpath(media_path + '_SG.mp4'),
			'webm': os.path.normpath(media_path + '_SG.webm'),
			'version': version,
			}
			
		#over-ride input path if given in args
		if input_path:
			self._media_paths.update({'input': input_path})	
	
		try:
			fps = int(version['sg_uploaded_movie_frame_rate'])
		except:
			fps = 30 # default value if none set
		
		#avoid pythonista trying to call ffmpeg :)
		if not ipad:
	
			if os.name == 'nt':
				ffmpeg = os.path.normpath('M:\\applications\\utilties\\ffmpeg\\bin\\ffmpeg.exe') 
			else:
				ffmpeg = os.path.normpath('/Applications/utilties/ffmpeg/bin/ffmpeg') 
				
			rate = ' -r %s ' %fps
			
			if version['sg_first_frame'] is not 'None':
				i_path = self._os_root + self._media_paths['input'][:-8] + str(version['sg_first_frame']).zfill(4) + '.exr'
			else:
				i_path = self._os_root + self._media_paths['input'][:-8] + '0001.exr'
				
			self._echo("input path is: %s" %i_path)
			if os.path.exists(i_path):
		
				#create prores master
				vcodec = ' -pix_fmt yuv422p10le -vcodec prores -profile:v 2 -vendor ap10 -filter:v scale="1280:trunc(ow/a/2)*2"'
				acodec = ' -acodec pcm_s16le -ar 48k'
				commandline = ffmpeg + rate + '-i ' + self._os_root + self._media_paths['input'] + vcodec + acodec + rate + self._os_root + self._media_paths['mov']
				subprocess.call(commandline)
			
				#create mp4 for SG
				vcodec = ' -pix_fmt yuv420p -vcodec libx264 -filter:v scale="1280:trunc(ow/a/2)*2" -b:v 4000k -vprofile high -bf 0 -strict experimental'
				acodec = ' -acodec aac -ab 160k -ac 2'
				commandline = ffmpeg + rate + '-i ' + self._os_root + self._media_paths['input'] + vcodec + acodec + rate + self._os_root + self._media_paths['mp4']
				subprocess.call(commandline)
			
				#create webm for SG
				vcodec = ' -pix_fmt yuv420p -vcodec libvpx -filter:v scale="1280:trunc(ow/a/2)*2" -b:v 4000k -quality realtime -cpu-used 0 -qmin 10 -qmax 42'
				acodec = ' -acodec libvorbis -aq 60 -ac 2'
				commandline = ffmpeg + rate + '-i ' + self._os_root + self._media_paths['input'] + vcodec + acodec + rate + self._os_root + self._media_paths['webm']
				subprocess.call(commandline)
				
			else:
				self._echo("Input path does not exist. Could not create media")
		
		status = {} 
		for key in self._media_paths.iterkeys():
			if key in ['mov','mp4','webm']:
				m_path = self._os_root + self._media_paths[key]
				if os.path.exists(m_path):
					status.update({key: True})
				else:
					status.update({key: False})
	
		self._echo("media creation status: ", status)
		self._media_paths.update({'status': status})
		return self._media_paths
		
	
	def update_version(self, paths = {}):
		
		# use input paths if given
		if paths:
			self._media_paths = paths
		if not self._media_paths:
			self._echo("version and associated media paths not set or given. Version NOT updated")
			return
			
		if os.name == 'nt':
			self._os_root = 'X:' + os.sep
		else:
			self._os_root = os.sep + 'Output' + os.sep
	
		# set urls
		url_root = 'http://yogi.axis.rocks/'
	
		local_link = {}
		if self._media_paths['status']['mov']:
			local_link = {
				'local_path': self._os_root + self._media_paths['mov'],
				'name': self._media_paths['version']['code'] + '.mov',
				'content_type': 'video/quicktime',
				'link_type': 'local',
				}

		mp4_link = {}
		if self._media_paths['status']['mp4']:				
			mp4_link = {
				'url': url_root + self._media_paths['mp4'].replace('\\','/'),
				'name': self._media_paths['version']['code']  + '_SG.mp4',
				'content_type': 'video/mp4',
				'link_type': 'web',
				}

		webm_link = {}
		if self._media_paths['status']['webm']:				
			webm_link = {
				'url': url_root + self._media_paths['webm'].replace('\\','/'),
				'name': self._media_paths['version']['code'] + '_SG.webm',
				'content_type': 'video/webm',
				'link_type': 'web',
				}

		if local_link and mp4_link and webm_link:
			data = {
				'sg_path_to_frames': self._os_root + self._media_paths['input'],
				'sg_path_to_movie': self._os_root + self._media_paths['mov'],
				'sg_uploaded_movie_mp4': mp4_link,
				'sg_uploaded_movie_webm': webm_link,
				'sg_uploaded_movie_transcoding_status': 1,
				'sg_status_list': 'rfr',
				}
		
			if not ipad:
				data.update({'sg_qt': local_link})
		
			updates = self._sg.update("Version", self._media_paths['version']['id'], data)
			self._echo("Media paths updated on Version %s:" %self._media_paths['version']['code'], updates)
	
		else:
			self._echo("Media was not encoded. Version %s NOT updated" %self._media_paths['version']['code'])
	
	
	def _set_user(self, u_data):
		if 'id' or 'name' or 'code' or 'login' or 'email' in u_data:
			fields = ['id','code','name','login','email']
			filters = []
			for key, value in u_data.iteritems():
				filters.append([key, 'is', value])
			return self._sg.find_one('HumanUser', filters, fields)
	
	
	# controls on internal printing of status to stdout	
	def echo_on(self):
		self._echo_state = True
		self._echo("echo is on")
		
	def echo_off(self):
		self._echo("echo is off")
		self._echo_state = False 
		
	def _echo(self, message = '', *args):
		if self._echo_state:
			print message + '\n'
		if args:
			pprint(args)
			print ''



	
	
# run tests if run as script

if __name__ == '__main__':
	
	# pythonista specific console commands
	if ipad:
		console.clear()
		console.show_activity()
	
	# test data
	
	context = (
		'Shot',
		'S0001',
		'sc01',
		'sh010',
		'Lighting',
		)
		
	v_data = {
		'user': {'name': 'Stu Aitken'},
		'note': 'this version added via SGVersionTools %s' %__version__,
		'in': 0,
		'out': 86,
		'fps': 30,
		}
		
	# open connection and find the first version for data in context()
	test = sg_version(context)
	shot = test.find_one(1)
	pprint(shot)
	
	# create a new version using V_data{}
	new_version = test.create_version(v_data)
	pprint (new_version)
	
	# create media and update the new version - this will fail as the input frames don't exist
	shot_path = test.create_media(new_version)
	test.update_version(shot_path)

