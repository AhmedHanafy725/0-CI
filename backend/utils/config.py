import toml


class ValidationError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class Configs:
    def __init__(self, **kwargs):
        self._config = self._from_file("../config.toml")
        self._load()

    def _load(self):
        self.iyo_id = self._config["iyo"]["id"]
        self.validate(self.iyo_id, str)
        self.iyo_secret = self._config["iyo"]["secret"]
        self.validate(self.iyo_secret, str)
        self.domain = self._config["main"]["domain"]
        self.validate(self.domain, str)
        self.result_path = self._config["main"]["result_path"]
        self.validate(self.result_path, str)
        self.chat_id = self._config["telegram"]["chat_id"]
        self.validate(self.chat_id, str)
        self.bot_token = self._config["telegram"]["token"]
        self.validate(self.bot_token, str)
        self.vcs_host = self._config["vcs"]["host"]
        self.validate(self.vcs_host, str)
        self.vcs_type = self._get_vcs_type()
        self.vcs_token = self._config["vcs"]["token"]
        self.validate(self.vcs_token, str)
        self.repos = self._config["vcs"]["repos"]
        self.validate(self.repos, list)
        self.db_name = self._config["db"]["name"]
        self.validate(self.db_name, str)
        self.db_host = self._config["db"]["host"]
        self.validate(self.db_host, str)
        self.db_port = self._config["db"]["port"]
        self.validate(self.db_port, int)
        self.environment = self._config["environment"]
        self.validate(self.environment, dict)

    def _from_file(self, filepath):
        try:
            config = toml.load(filepath)
        except toml.TomlDecodeError as e:
            raise ConfigurationError(e)
        return config

    def validate(self, value, type):
        if not isinstance(value, type):
            raise ValidationError(f"{value} should be {type}")

    def _get_vcs_type(self):
        if "github" in self.vcs_host:
            vcs_type = "github"
        else:
            vcs_type = "gitea"
        return vcs_type
