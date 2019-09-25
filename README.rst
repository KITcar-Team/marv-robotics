
Server
=============

- marv: publishes on port 8450
- nginx: rosbags.kitcar-team.de to 8450

workflow
=============
- working branch is kitcar_master
- If you want to update the master, first merge newest master, than REBASE kitcar_master

- ``su marv-user`` Every file should belong to marv user. 
- If something is root: go to ``/home/marv-user``  and run ``sudo chown -R marv-user:marv-user marv-robotics/``
- on server@root: git repro cloned in ``/home/marv-user/``
- ``git push`` ->dockerhub builds docker-image automatic (takes ~20 min.)
- on server@root: ``docker pull kitcar/marv-robotics``  to pull branches: ``docker pull kitcar/marv-robotics:YOURBRANCHNAME``

- ``exit``-> will be user root again the container needs to be started with root
- on server@root(master): `./scripts/run-container sites/KITcar --detach` for debugging, omit --detatch
- site now avaiable at rosbags.kitcar-team.de > login with ldap credentials 
- ``su marv-user``
- on server@marv-user(master): ``./scripts/enter-container`` Enter the container see below

!The first login with ldap creates a user in the sqldatabase which was intendet to be the
database to store user and password. This is to have an minimal invasive change of the original code.
Thus all actions like commenting on Rosbags are still managed by the original Database system.

Config
=============
deprecated! We use ldap instead. No need to add user. Users added like this wont be able to log in. <br/> 
- ``./scripts/enter-container``   					enter container
- ``$container: marv user add kitcar``				User anlegen -> password festlegen 
- ``$container: marv group adduser kitcar admin`` 	mache user einen admin

Scan bags
=============
- ``./scripts/enter-container``   		enter container
- ``marv scan`` 							scan the bag folder for new bags
- ``$container: marv run --col=*``  		do the processing of the new found
Scanners are called for every directory within the configured scanroots, while files and directories starting with a . and directories containing an (empty) .marvignore file are ignored and will not be traversed into.

work on an git branch
=============
To hook the right image, you have to change in file `scripts/run-container` the line <br/> 
```
IMAGE="kitcar/marv-robotics:kitcar_master"  <br/>
```
to  <br/>
```
IMAGE="kitcar/marv-robotics:branchname" <br/> 
```
!! But dont commit this change into master !!  


plugins
=============
- ``./scripts/enter-container``  			enter container
- ``$container: marv run --list-nodes`` 	shows all nodes

located in /marv-robotics/code/marv-robotics/  
unit tests: /marv-robotics/code/marv-robotics/tests/  
https://rosbags.kitcar-team.de/docs/tutorial/write-your-own.html  
https://rosbags.kitcar-team.de/docs/tutorial/setup-basic-site.html  

- yourPlugin.py
    * add plugin: ``nano /marv-robotics/sites/KITcar/marv.conf``
    * add your node under >> nodes = <<  
    * marv_robotics.yourPlugin:defines
    * add your node under >> detail_sections = << 



original readme:
=============
MARV Robotics
=============

Welcome to the MARV Robotics Community Edition.

MARV Robotics is a powerful and extensible data management platform,
featuring a rich dynamic web interface, driven by your algorithms,
configurable to the core, and integrating well with your tools to
supercharge your workflows.

For more information please see:

- MARV Robotics `documentation <https://ternaris.com/marv-robotics/docs/>`_
- MARV Robotics `website <https://ternaris.com/marv-robotics/>`_

Quickstart
==========

Clone repository and tell scripts that you want to use the official MARV Robotics CE image. Alternatively, you can build it yourself with ``./scripts/build-image``, in which case you don't create the ``.image-name`` file.

::

   git clone git@github.com:ternaris/marv-robotics
   cd marv-robotics
   echo ternaris/marv-robotics > .image-name

Start container.

::

  ./scripts/run-container sites/example path/to/bags  !! KITcar:: dont pass path/to/bags, its in the run-container script

There should be a couple of uwsgi workers waiting to serve requests and MARV Robotics is now running at: https://localhost:8000/

If the container fails to start with *Permission denied*::

  [Errno 13] Permission denied: '/home/marv/site/sessionkey'

most likely the uid of your user outside docker does not match the one inside (1000). See `Docker <https://ternaris.com/marv-robotics/docs/install/docker.html>`_ on how to build a custom image with matching uid and gid.
!! KITcar our marv-user has uid and gid 1001 and is in group docker

Additional arguments are passed as options to ``docker run``, e.g.

::

   ./scripts/run-container sites/example path/to/bags --detach !! KITcar:: dont pass path/to/bags, its in the run-container script

Enter the container, scan for datasets and run nodes.

::

   ./scripts/enter-container  !! KITcar:: only possible when logged in as marv-user

::

   marv scan
   marv run --col=*

Add a user to add tags and comments.

::

   marv user add zaphod

Make the user a member of the admin group in order to discard datasets. With the next ``marv scan`` discarded datasets are re-added as new datasets; all data previously associated with them is deleted.

::

   marv group adduser zaphod admin

So far, only tooling and the example site are used from the repository.

For more information see our `Docker <https://ternaris.com/marv-robotics/docs/install/docker.html>`_ installation instructions.

Alternatively, you can follow the `Native <https://ternaris.com/marv-robotics/docs/install/native.html>`_ installation instructions.

Contributing
============

Thank you for considering to contribute to MARV.

To submit issues or create merge requests please follow the
instructions provided in the `contribution guide
<./CONTRIBUTING.rst>`_.

By contributing to MARV you accept and agree to the terms and
conditions laid out in there.

