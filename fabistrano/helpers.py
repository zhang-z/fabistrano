from os import path
import functools
from fabric.api import run, env, sudo


def dir_exists(dir_path):
    # why this line was comment out?
    return run('[ -d %s ] && echo 1 || echo 0' % dir_path) == '1'


def set_defaults():
    if '_fabi_defaults' in env:
        return
    domain_path = path.join(env.base_dir, env.app_name)
    # domain_path must be set separately, since it's referred in other defaults
    env.setdefault('domain_path', domain_path)
    defaults = (
        ('use_sudo', True),
        ('git_branch', 'master'),
        ('svn_revision', 'HEAD'),
        ('svn_username', ''),
        ('svn_password', ''),
        ('python_bin', 'python'),
        ('remote_owner', 'www-data'),
        ('remote_group', 'www-data'),
        ('update_env', False), # Default to False, as we are removing this function.
        ('deploy_via', 'remote_clone'),
        ('current_path', path.join(env.domain_path, 'current')),
        ('releases_path', path.join(env.domain_path, 'releases')),
        ('shared_path', path.join(env.domain_path, 'shared')),
        # The following dirs will be created in shared_path when setting up.
        # During deployment, these dirs will be soft-linked
        # from shared_path to the current dir.
        ('shared_dirs', ['log', 'static']),
    )
    for k, v in defaults:
        env.setdefault(k, v)

    if dir_exists(env.releases_path):
        # The current_release and previous_release set here
        # are for RollBackTask. For deploy, set new value
        # for current_release in your strategy.

        env.releases = sorted(run('ls -x %(releases_path)s' % {'releases_path': env.releases_path}).split())

        if len(env.releases) >= 1:
            env.current_revision = env.releases[-1]
            env.current_release = '%(releases_path)s/%(current_revision)s' % \
                                  {'releases_path': env.releases_path,
                                   'current_revision': env.current_revision}
        if len(env.releases) > 1:
            env.previous_revision = env.releases[-2]
            env.previous_release = '%(releases_path)s/%(previous_revision)s' % \
                                   {'releases_path': env.releases_path,
                                    'previous_revision': env.previous_revision}

    env._fabi_defaults = True


def sudo_run(*args, **kwargs):
    if env.use_sudo:
        sudo(*args, **kwargs)
    else:
        run(*args, **kwargs)
