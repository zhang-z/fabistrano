from os import path
from time import time
from fabric.api import env, local, put, cd
from fabistrano.helpers import sudo_run


def prepare_for_checkout():
    # Set current timestamp as the name of release
    env.current_revision = str(int(time()))
    env.current_release = '%(releases_path)s/%(current_revision)s' % {'releases_path':env.releases_path, 'current_revision':env.current_revision}


# Git
def remote_clone():
    """Checkout code to the remote servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = '%(app_name)s_%(branch_name)s_%(current_revision)s.tar.bz2' % {
        'app_name': env.app_name,
        'branch_name': env.git_branch,
        'current_revision': env.current_revision,}
    
    local_cache = '/tmp/'+cache_name
    
    sudo_run('git archive --remote=%(git_clone)s %(git_branch)s | bzip2 > %(local_cache)s' % {
        'git_clone': env.git_clone,
        'git_branch': env.git_branch,
        'local_cache': local_cache,})
    
    sudo_run('mkdir -p %(current_release)s' % {
        'current_release': env.current_release,})
    
    with cd(env.current_release):
        sudo_run('tar jxf %(local_cache)s' % {
            'local_cache': local_cache,
        })


def local_clone():
    """Checkout code to local machine, then upload to servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = '%(app_name)s_%(branch_name)s_%(current_revision)s.tar.bz2' % {
        'app_name': env.app_name,
        'branch_name': env.git_branch,
        'current_revision': env.current_revision,}
    
    local_cache = '/tmp/' + cache_name
    
    local('git archive --remote=%(git_clone)s %(git_branch)s | bzip2 > %(local_cache)s' % {
        'git_clone': env.git_clone,
        'git_branch': env.git_branch,
        'local_cache': local_cache,})
    
    put(local_cache, '/tmp/')
    
    sudo_run('mkdir -p %(current_release)s' % {
        'current_release': env.current_release,})
    
    with cd(env.current_release):
        sudo_run('tar jxf %(local_cache)s' % {
            'local_cache': local_cache,
        })


# SVN
def remote_export():
    """Checkout code to the remote servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = '%(app_name)s_%(svn_revision)s_%(current_revision)s' % {
        'app_name': env.app_name,
        'svn_revision': env.svn_revision,
        'current_revision': env.current_revision,}
    
    local_cache = '/tmp/'+cache_name
    
    # svn auth
    svn_username_opt = ''
    if env.svn_username:
        svn_username_opt = '--username %(svn_username)s' % {'svn_username':env.svn_username}
    
    svn_password_opt = ''
    if env.svn_password:
        svn_password_opt = '--password %(svn_password)s' % {'svn_password':env.svn_password}
    
    sudo_run('svn export -r %(svn_revision)s %(svn_repo)s %(local_cache)s %(svn_username_opt)s %(svn_password_opt)s' % {
        'svn_revision': env.svn_revision,
        'svn_repo': env.svn_repo,
        'local_cache': local_cache,
        'svn_username_opt': svn_username_opt,
        'svn_password_opt': svn_password_opt,})
    
    sudo_run('mv %(local_cache)s %(current_release)s' % {
        'local_cache': local_cache,
        'current_release': env.current_release,
    })


def local_export():
    """Checkout code to local machine, then upload to servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = '%(app_name)s_%(svn_revision)s_%(current_revision)s' % {
        'app_name': env.app_name,
        'svn_revision': env.svn_revision,
        'current_revision': env.current_revision,}
    
    # svn auth
    svn_username_opt = ''
    if env.svn_username:
        svn_username_opt = '--username %(svn_username)s' % {'svn_username':env.svn_username}
    
    svn_password_opt = ''
    if env.svn_password:
        svn_password_opt = '--password %(svn_password)s' % {'svn_password':env.svn_password}
    
    local('svn export -r %(svn_revision)s %(svn_repo)s /tmp/%(cache_name)s %(svn_username_opt)s %(svn_password_opt)s' % {
        'svn_revision': env.svn_revision,
        'svn_repo': env.svn_repo,
        'cache_name': cache_name,
        'svn_username_opt': svn_username_opt,
        'svn_password_opt': svn_password_opt,})
    
    local('cd /tmp/ && tar cvzf %(cache_name)s.tar.gz %(cache_name)s' % {
        'cache_name': cache_name,
        })
    
    put('/tmp/%(cache_name)s.tar.gz' % {'cache_name': cache_name}, '/tmp/')
    
    with cd('/tmp'):
        sudo_run('tar -xvf %(cache_name)s.tar.gz' % {
            'cache_name': cache_name,
            })
        
        sudo_run('mv %(cache_name)s %(current_release)s' % {
            'cache_name': cache_name,
            'current_release': env.current_release,
        })

