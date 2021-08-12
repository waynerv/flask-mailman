class ConfigError(Exception):
    def __init__(self, message):
        """
        riase this eror if any required config is missing.
        """
        super(ConfigError, self).__init__(message)