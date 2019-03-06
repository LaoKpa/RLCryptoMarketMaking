import configparser as cp

BAD_CONFIGURATION_NAME = 'No Such Configuration.'

class ConfigHelper(object):
	def __init__(self, configPath, configName):
		self.parser = cp.ConfigParser()
		self.parser.read(configPath)
		if not configName in self.parser.sections():
			raise Exception(BAD_CONFIGURATION_NAME)
		configTuples = [(var, self.getAttribute(configName, var)) for var in self.parser.options(configName)]
		for var, val in configTuples:
			setattr(self, var, val)

	def getAttribute(self,configName, var):
		try:
			return self.parser.getint(configName, var)
		except Exception as e:
			pass
		try:
			return self.parser.getfloat(configName, var)
		except Exception as e:
			pass
		try:
			return self.parser.getboolean(configName, var)
		except Exception as e:
			pass
		return self.parser.get(configName, var)
