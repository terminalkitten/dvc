import argparse
import os

from dvc.git_wrapper import GitWrapper
from dvc.config import Config, ConfigError
from dvc.logger import Logger
from dvc.path_factory import PathFactory
from dvc.utils import cached_property


class CmdBase(object):
    CONFIG = 'dvc.conf'

    def __init__(self, parse_config=True):
        self._git = GitWrapper()
        self._args = None
        self._dvc_home = None

        self._config = None
        if parse_config:
            self._config = Config(os.path.realpath(os.path.join(self.git.git_dir, self.CONFIG)))

        parser = argparse.ArgumentParser()
        self.define_args(parser)
        self._args, self._args_unkn = parser.parse_known_args()

        self._dvc_home = os.environ.get('DVC_HOME')

        if not self.lnx_home:
            raise ConfigError('DVC_HOME environment variable is not defined')
        if not os.path.exists(self._dvc_home):
            raise ConfigError("DVC_HOME directory doesn't exists")
        pass

    @cached_property
    def path_factory(self):
        return PathFactory(self.git, self.config)

    @property
    def config(self):
        return self._config

    def cache_file_aws_key(self, file):
        return '{}/{}'.format(self._config.aws_storage_prefix, file).strip('/')

    @property
    def lnx_home(self):
        return self._dvc_home

    @property
    def args(self):
        return self._args

    @property
    def git(self):
        return self._git

    def define_args(self, parser):
        pass

    def set_skip_git_actions(self, parser):
        parser.add_argument('--skip-git-actions', '-s', action='store_true',
                            help='skip all git actions including reproducibility check and commits')

    @property
    def skip_git_actions(self):
        return self.args.skip_git_actions

    @staticmethod
    def not_committed_changes_warning():
        Logger.warn('Warning: changes were not committed to git')

    def add_string_arg(self, parser, name, message, default = None,
                       conf_section=None, conf_name=None):
        if conf_section and conf_name:
            section = self.config[conf_section]
            if not section:
                raise ConfigError("")
            default_value = section.get(conf_section, default)
        else:
            default_value = default

        parser.add_argument(name,
                            metavar='',
                            default=default_value,
                            help=message)

    def run(self):
        pass

    def get_cache_file_s3_name(self, cache_file):
        cache_prefix_file_name = os.path.relpath(os.path.realpath(cache_file), os.path.realpath(self.git.git_dir))
        file_name = os.path.relpath(cache_prefix_file_name, self.config.cache_dir)
        nlx_file_path_trim = file_name.replace(os.sep, '/').strip('/')
        return self.config.aws_storage_prefix + '/' + nlx_file_path_trim