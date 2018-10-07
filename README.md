ECR DOCKER CI
============

## Usage

ecr-docker-ci is a standalone build flow tool for Docker. It is a command line tool that builds Docker images based on their Dockerfile and a .ecr-docker-ci.yml.

ecr-docker-ci uses a yml file as a descriptor for actions. Here is an example:

```json
Global:
  actions:
    - build
    - push
    - push_to_ecr

Amazon ECR:
  aws_access_key_id: 'SECRET'
  aws_secret_access_key: 'SECRET'
  region_name: 'us-west-2'
  ecr_repo_name: 'company/image'

Docker:
  tag: 'test_docker_image:v0.1'

```
 Each action is independent of the other ones and downstream steps can use upstream ones as source. Some actions require specific configurations isolated in diferents sections.

For `push_to_ecr` action we need create a section 'Amazon ECR' like to shows the example.

For `build` an `push` actions we need create a section 'Docker' the parameters available in this section are:


* `path (str)` – Path to the directory containing the Dockerfile
* `fileobj` – A file object to use as the Dockerfile. (Or a file-like object)
* `tag (str)` – A tag to add to the final image
* `quiet (bool)` – Whether to return the status
* `nocache (bool)` – Don’t use the cache when set to True
* `rm (bool)` – Remove intermediate containers. The docker build command now defaults to --rm=true, but we have kept the old default of False to preserve backward compatibility.
* `timeout (int)` – HTTP timeout
* `custom_context (bool)` – Optional if using fileobj
* `encoding (str)` – The encoding for a stream. Set to gzip for compressing
* `pull (bool)` – Downloads any updates to the FROM image in Dockerfiles
* `forcerm (bool)` – Always remove intermediate containers, even after unsuccessful builds
* `dockerfile (str)` – path within the build context to the Dockerfile
* `buildargs (dict)` – A dictionary of build arguments
* `container_limits (dict)` –
A dictionary of limits applied to each container created by the build process. Valid keys:
  * `memory (int)`: set memory limit for build
  * `memswap (int)`: Total memory (memory + swap), -1 to disable
swap
  * `cpushares (int)`: CPU shares (relative weight)
  * `cpusetcpus (str)`: CPUs in which to allow execution, e.g.,"0-3", "0,1".
  * `decode (bool)` – If set to True, the returned stream will be decoded into dicts on the fly. Default False.
* `cache_from (list)` – A list of images used for build cache resolution.


ecr-docker-ci can be ran in your own computer (Python support its must).

## Development

ecr-docker-ci is builded inside a Python 2.7 virtualenv, the `Makefile` file can help us to create packages for a most popular distributions (RPM/DEB/APK).

For an easy development flow I created a Vagrant environment based on Debian Jessie with all ecr-docker-ci's needs to made. The previous requeriments to launch the Vagrant enviorment are:
* Virtualbox
* Vagrant
* vagrant-vbguest plugin (`vagrant plugin install vagrant-vbguest`)

For launching the Vagrant environment you should type into your terminal: `vagrant up --provision` after bootstrapping ends you can access to environment using `vagrant ssh`.

If you won't use the Vagrant environment, you can use directly the Makefile file to building packages, the only requeriments needed are `docker-daemon`, `docker-client` and of course `make.
