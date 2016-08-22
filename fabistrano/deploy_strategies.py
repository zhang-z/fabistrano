import os.path
from datetime import datetime
import uuid
from fabric.api import env, local, put, cd, run
from fabistrano.helpers import sudo_run


def prepare_for_checkout():
    # Set current datetime_sha1 as the name of release
    # use first 7 chars of commit hash
    # Append user to end of string, for avoiding permission conflict.
    git_cmd = 'git ls-remote %(git_clone)s %(git_branch)s' % {
        'git_clone': env.git_clone, 'git_branch': env.git_branch,
    }
    commit_hash = local(git_cmd, capture=True).split('\t')[0]
    env.commit_hash = commit_hash
    env.current_revision = datetime.now().strftime('%Y%m%d_%H%M%S_') + commit_hash[:7] + "_" + str(env.user)
    env.current_release = '%(releases_path)s/%(current_revision)s' % {
        'releases_path': env.releases_path, 'current_revision': env.current_revision,
    }


# Git
def remote_clone():
    """Checkout code to the remote servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = 'code_%s.tar.bz2' % env.commit_hash[:15]
    
    local_cache = '/tmp/'+cache_name
    
    sudo_run('git archive --remote=%(git_clone)s %(git_branch)s | bzip2 > %(local_cache)s' % {
        'git_clone': env.git_clone,
        'git_branch': env.git_branch,
        'local_cache': local_cache,
    })
    
    sudo_run('mkdir -p %(current_release)s' % {
        'current_release': env.current_release,
    })
    
    with cd(env.current_release):
        sudo_run('tar jxf %(local_cache)s' % {
            'local_cache': local_cache,
        })


def local_clone():
    """Checkout code to local machine, then upload to servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = 'code_%s.tar.bz2' % env.commit_hash[:15]
    
    local_cache = '/tmp/' + cache_name

    if not os.path.isfile(local_cache):
        local('git archive --remote=%(git_clone)s %(git_branch)s | bzip2 > %(local_cache)s' % {
            'git_clone': env.git_clone,
            'git_branch': env.git_branch,
            'local_cache': local_cache,
        })
    
    put(local_cache, '/tmp/')
    
    sudo_run('mkdir -p %(current_release)s' % {
        'current_release': env.current_release,
    })
    
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
    cache_name = 'code_%(app_name)s_%(svn_revision)s_%(current_revision)s' % {
        'app_name': env.app_name,
        'svn_revision': env.svn_revision,
        'current_revision': env.current_revision,
    }
    
    local_cache = '/tmp/'+cache_name
    
    # svn auth
    svn_username_opt = ''
    if env.svn_username:
        svn_username_opt = '--username %(svn_username)s' % {'svn_username': env.svn_username}
    
    svn_password_opt = ''
    if env.svn_password:
        svn_password_opt = '--password %(svn_password)s' % {'svn_password': env.svn_password}
    
    sudo_run('svn export -r %(svn_revision)s %(svn_repo)s %(local_cache)s %(svn_username_opt)s %(svn_password_opt)s' % {
        'svn_revision': env.svn_revision,
        'svn_repo': env.svn_repo,
        'local_cache': local_cache,
        'svn_username_opt': svn_username_opt,
        'svn_password_opt': svn_password_opt,
    })
    
    sudo_run('mv %(local_cache)s %(current_release)s' % {
        'local_cache': local_cache,
        'current_release': env.current_release,
    })


def local_export():
    """Checkout code to local machine, then upload to servers"""
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = 'code_%(app_name)s_%(svn_revision)s_%(current_revision)s' % {
        'app_name': env.app_name,
        'svn_revision': env.svn_revision,
        'current_revision': env.current_revision,
    }
    
    # svn auth
    svn_username_opt = ''
    if env.svn_username:
        svn_username_opt = '--username %(svn_username)s' % {'svn_username': env.svn_username}
    
    svn_password_opt = ''
    if env.svn_password:
        svn_password_opt = '--password %(svn_password)s' % {'svn_password': env.svn_password}

    cmd = ('svn export -r %(svn_revision)s %(svn_repo)s '
           '/tmp/%(cache_name)s %(svn_username_opt)s %(svn_password_opt)s') % {
        'svn_revision': env.svn_revision,
        'svn_repo': env.svn_repo,
        'cache_name': cache_name,
        'svn_username_opt': svn_username_opt,
        'svn_password_opt': svn_password_opt,
    }
    local(cmd)
    
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


def localcopy():
    """ Deploy local copy to servers """
    # set new release env
    prepare_for_checkout()
    
    # start
    cache_name = 'code_%s.tar.bz2' % env.commit_hash[:15]
    
    cmd = ('cp -rf %(localcopy_path)s /tmp/%(cache_name)s && '
           'cd /tmp/ && tar cvzf %(cache_name)s.tar.gz %(cache_name)s') % {
        'localcopy_path': env.localcopy_path,
        'cache_name': cache_name,
    }
    local(cmd)
    
    # We add a guid for tmp folder on server is to avoid conflict
    # when deploying onto localhost, mainly for testing purpose.
    server_tmp_folder = '/tmp/%(guid)s' % {'guid': uuid.uuid4().hex}
    
    sudo_run('mkdir -p %(dir)s && chmod 777 %(dir)s' % {'dir': server_tmp_folder})
    
    put('/tmp/%(cache_name)s.tar.gz' % {'cache_name': cache_name}, server_tmp_folder)
    
    with cd(server_tmp_folder):
        sudo_run('tar -xvf %(cache_name)s.tar.gz' % {
            'cache_name': cache_name,
            })
        
        sudo_run('mv %(cache_name)s %(current_release)s' % {
            'cache_name': cache_name,
            'current_release': env.current_release,
        })
