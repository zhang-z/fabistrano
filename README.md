fabistrano
============

Fabistrano is a set of [Fabric](http://docs.fabfile.org/en/1.6/) tasks that allows you to do [Capistrano](https://github.com/capistrano/capistrano) style deployments for python web apps.

## What is a _capistrano style_ deployment?

Capistrano deploys code under versioned directories and then symlinks the latest one as the *current* release.

A sample structure would look like this:

  ```
    app.com
    |
    | - releases
      | - 1366924759
      | - 1366927898
      | - 1367155641
    | - shared
    | - current
  ```

## Why use this style of deployment?

Using fabistrano you get the following benefits:

- Scripted and ordered deployments
- Very low downtime when deploying new code
- Easy roll backs

## Usage

1. Install fabistrano:

` pip install fabistrano `

2. In your `fabfile.py` you need to import fabistrano and set the environment variables:

  ```
    from fabric.api import env
    from fabistrano import deploy


    env.hosts = ["HOST"] # Replace with your host name or IP
    env.base_dir = '/www' # Set to your app's directory
    env.app_name = 'app_name.com' # This will deploy the app to /www/app_name.com/
    env.git_clone = 'GIT_PATH' # Your git url

    env.restart_cmd = 'kill -HUP `supervisorctl pid gunicorn`' # Restart command
    # or
    # env.wsgi_path = "app_name/apache.wsgi" # Relative path to the wsgi file to be touched on restart
  ```


3. Run `setup` to create the directory structure:

  ` fab deploy.setup `

4. Deploy the app:

  ` fab deploy `

5. Setup your web server to point to the `current` directory.


And you should be good to go!

## Deploy Strategy

There are 5 strategies you can use for deployment.

1. Git archive on remote servers.
  ```
    env.deploy_via = 'remote_clone'
    env.git_clone  = 'GIT_PATH' # Your git url
  ```

2. Git archive on local machine and then upload to remote servers.
  ```
    env.deploy_via = 'local_clone'
    env.git_clone  = 'GIT_PATH' # Your git url
  ```

3. SVN export on remote servers.
  ```
    env.deploy_via   = 'remote_export'
    env.svn_repo     = 'SVN REPO URL'
    env.svn_username = 'SVN USERNAME' # optinal
    env.svn_password = 'SVN PASSWORD' # optinal
  ```

4. SVN export on local machine and then upload to remote servers.
  ```
    env.deploy_via   = 'local_export'
    env.svn_repo     = 'SVN REPO URL'
    env.svn_username = 'SVN USERNAME' # optinal
    env.svn_password = 'SVN PASSWORD' # optinal
  ```

5. Archive a copy on local machine and upload to remote servers to deploy.
  ```
    env.deploy_via   = 'localcopy'
    env.localcopy_path = '/project/path/on/your/pc/name_xyz'
  ```

## Environment Variables

- shared_dirs - list, default: ['log']
  ```python
    # List of dir names which will be created in shared folder during setup.
    # These dirs will be soft-linked to current release during each deployment.
    # Default: ['log']
    # You can override in your own settings:
    shared_dirs = ['log', 'static', 'tmp']
  ```

## Current status

This tool is under active development and you might see errors.

## License

The template itself is available under the "Simplified" BSD license and can be
freely modified under the terms of that license. You can see the
[full license text](https://github.com/dlapiduz/fabistrano/blob/master/LICENSE>)
in the Github repository for additional detail.

Applications created using this template are not considered derivatives works.
Applications created using this template can be freely licensed under whatever
you as the author chooses. They may be either open or closed source.

