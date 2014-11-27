from os import path
from time import time
from fabric.api import env, run, local, put, cd


def prepare_for_checkout():
    env.current_release = '%(releases_path)s/%(time).0f' % \
                          {'releases_path': env.releases_path, 'time': time()}
    if 'commit_id' not in env:
        env.commit_id = local('git rev-parse --short origin/%s' % env.git_branch, capture=True)


def remote_clone():
    """Checkout code to the remote servers"""
    prepare_for_checkout()
    run('cd %(releases_path)s; git clone -b %(git_branch)s -q %(git_clone)s %(current_release)s' %
        {'releases_path': env.releases_path,
         'git_clone': env.git_clone,
         'current_release': env.current_release,
         'git_branch': env.git_branch})


def local_clone():
    """Checkout code to local machine, then upload to servers"""
    prepare_for_checkout()
    cache_name = '%(app_name)s_%(commit_id)s.tar.bz2' %\
                 {'app_name': env.app_name, 'commit_id': env.commit_id}
    local_cache = '/tmp/' + cache_name
    if not path.exists(local_cache):
        local('git archive --remote=%(git_clone)s %(git_branch)s | bzip2 > %(local_cache)s' %
              {'git_clone': env.git_clone,
               'git_branch': env.git_branch,
               'local_cache': local_cache})
    put(local_cache, '/tmp/')
    run('mkdir -p %s' % env.current_release)
    with cd(env.current_release):
        run('tar jxf /tmp/%s' % cache_name)
