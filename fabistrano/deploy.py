from fabric.api import env, run
from fabric.tasks import Task
from fabistrano.helpers import set_defaults, sudo_run


VERSION = "0.4"

env.timeout = 6000


class BaseTask(Task):
    def __init__(self, *args, **kwargs):
        super(BaseTask, self).__init__(*args, **kwargs)

    def run(self):
        set_defaults()
        self.task()

    def task(self):
        raise NotImplementedError


class RestartTask(BaseTask):
    name = 'restart'

    def task(self):
        """Restarts your application"""
        try:
            run('touch %(current_release)s/%(wsgi_path)s' %
                {'current_release': env.current_release,
                 'wsgi_path': env.wsgi_path})
        except AttributeError:
            try:
                sudo_run(env.restart_cmd)
            except AttributeError:
                pass

restart = RestartTask()


def permissions():
    """Make the release group-writable"""
    sudo_run('chown -R %(user)s:%(group)s %(domain_path)s' %
             {'domain_path': env.domain_path,
              'user': env.remote_owner,
              'group': env.remote_group})
    sudo_run('chmod -R g+w %(domain_path)s' % {'domain_path': env.domain_path})


class SetupTask(BaseTask):
    name = 'setup'

    def task(self):
        """Prepares one or more servers for deployment"""
        sudo_run('mkdir -p %(domain_path)s/{releases,shared}' % {'domain_path': env.domain_path})
        sudo_run('mkdir -p %(shared_path)s/{system,log}' % {'shared_path': env.shared_path})
        permissions()

setup = SetupTask()


def checkout():
    """Checkout code to the remote servers"""
    from time import time
    env.current_release = '%(releases_path)s/%(time).0f' % {'releases_path': env.releases_path, 'time': time()}
    run('cd %(releases_path)s; git clone -b %(git_branch)s -q %(git_clone)s %(current_release)s' %
        {'releases_path': env.releases_path,
         'git_clone': env.git_clone,
         'current_release': env.current_release,
         'git_branch': env.git_branch})


class UpdateTask(BaseTask):
    name = 'update'

    def task(self):
        """Copies your project and updates environment and symlink"""
        UpdateCodeTask().run()
        update_env()
        symlink()
        set_current()
        permissions()

update = UpdateTask()


class UpdateCodeTask(BaseTask):
    name = 'update_code'

    def task(self):
        """Copies your project to the remote servers"""
        checkout()
        permissions()

update_code_task = UpdateCodeTask()


def symlink():
    """Updates the symlink to the most recently deployed version"""
    run('ln -nfs %(shared_path)s/log %(current_release)s/log' %
        {'shared_path': env.shared_path, 'current_release': env.current_release})


def set_current():
    """Sets the current directory to the new release"""
    run('ln -nfs %(current_release)s %(current_path)s' %
        {'current_release': env.current_release, 'current_path': env.current_path})


def update_env():
    """Update servers environment on the remote servers"""
    sudo_run('cd %(current_release)s; pip install -r requirements.txt' %
             {'current_release': env.current_release})
    permissions()


class CleanUpTask(BaseTask):
    name = 'cleanup'

    def task(self):
        """Clean up old releases"""
        if len(env.releases) > 3:
            directories = env.releases
            directories.reverse()
            del directories[:3]
            env.directories = ' '.join(['%(releases_path)s/%(release)s' %
                                        {'releases_path': env.releases_path, 'release': release} for release in directories])
            run('rm -rf %(directories)s' % {'directories': env.directories})

cleanup = CleanUpTask()


def rollback_code():
    """Rolls back to the previously deployed version"""
    if len(env.releases) >= 2:
        env.current_release = env.releases[-1]
        env.previous_revision = env.releases[-2]
        env.current_release = '%(releases_path)s/%(current_revision)s' %\
                              {'releases_path': env.releases_path, 'current_revision': env.current_revision}
        env.previous_release = '%(releases_path)s/%(previous_revision)s' %\
                               {'releases_path': env.releases_path, 'previous_revision': env.previous_revision}
        run('rm %(current_path)s; ln -s %(previous_release)s %(current_path)s && rm -rf %(current_release)s' %
            {'current_release': env.current_release, 'previous_release': env.previous_release, 'current_path': env.current_path})


class RollBackTask(BaseTask):
    name = 'rollback'

    def task(self):
        """Rolls back to a previous version and restarts"""
        rollback_code()
        RestartTask().run()

rollback = RollBackTask()


class DeployTask(BaseTask):
    name = 'deploy'
    is_default = True

    def task(self):
        """Deploys your project. This calls both `update' and `restart'"""
        UpdateTask().run()
        RestartTask().run()

deploy = DeployTask(default=True)
