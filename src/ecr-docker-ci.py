#!/usr/bin/python

'''
Author: Albert Monfa 2017

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import boto3
import os
import sys
import json
import re
import yaml
import logging
import logging.handlers
import docker
import argparse
from base64 import b64decode
from jsonschema import validate, ValidationError

# Constant subsystem
def constant(f):
    def fset(self, value):
        raise TypeError
    def fget(self):
        return f()
    return property(fget, fset)

class _Const(object):
    @constant
    def DEFAULT_CONF_FILE():
        return '.ecr_docker_ci.yml'
    @constant
    def APP_NAME_HELP():
        return 'ECR-docker-ci - Albert Monfa 2017'
    @constant
    def APP_NAME():
        return 'ECR-docker-ci'

# Config schemas
global_sch = {
               "definitions": {
                 "actions": {
                   "type": "array",
                   "items": {
                     "enum": [ "build", "push", "push_to_ecr" ]
                   }
                 }
               },
               "type": "object",
               "required": [ "Global"],
               "properties": {
                 "Global": {
                   "type": "object",
                   "required": ["actions"],
                   "properties": {
                     "actions": { "$ref": "#/definitions/actions" },
                   },
                   "additionalProperties": False
                 },
               },
             }
aws_sch    = {
               "definitions": {
	         "region_name": {
	           "oneOf": [
	             {  "type": "string", "pattern": "^us-east-1$" },
	             {  "type": "string", "pattern": "^us-east-2$" },
	             {  "type": "string", "pattern": "^us-west-1$" },
	             {  "type": "string", "pattern": "^us-west-2$" },
	             {  "type": "string", "pattern": "^ca-central-1$" },
	             {  "type": "string", "pattern": "^eu-central-1$" },
	             {  "type": "string", "pattern": "^eu-west-1$" },
	             {  "type": "string", "pattern": "^eu-west-2$" },
	             {  "type": "string", "pattern": "^ap-northeast-1$" },
	             {  "type": "string", "pattern": "^ap-southeast-1$" },
	             {  "type": "string", "pattern": "^ap-southeast-2$" }
	           ]
	         }
	       },
	       "type": "object",
	       "required": [ "Amazon ECR"],
	       "properties": {
	         "Amazon ECR": {
	           "type": "object",
	           "required": [ "aws_access_key_id",
	                         "aws_secret_access_key",
	                         "region_name",
	                         "ecr_repo_name"
	                       ],
	           "properties": {
	             "aws_access_key_id": {
	               "type": "string"
	             },
	             "aws_secret_access_key": {
	               "type": "string"
	             },
	             "region_name": {
	               "$ref": "#/definitions/region_name"
	             },
	             "ecr_repo_name": {
	               "type": "string"
	             }
	           },
	           "additionalProperties": False,
	         }
	       }
	     }
push_sch   = {
               "type": "object",
               "required": [ "Docker"],
               "properties": {
                 "Docker": {
                   "type": "object",
                   "required": [
                                 "tag"
                               ],
                   "properties": {
                     "tag": {
                       "type": "string"
                     },
                     "daemon": {
                       "type": "string",
                       "pattern": "^(unix:///|tcp://).*$"
                     }
                   }
                 }
               }
             }
build_sch  = {
	       "type": "object",
	       "required": [ "Docker"],
	       "properties" : {
	         "Docker": {
	           "type": "object",
	           "required": [
	                         "tag"
	                       ],
	           "properties": {
	             "daemon":           { "type": "string",
                                           "pattern": "^(unix:///|tcp://).*$" },
	             "tag":              { "type": "string" },
	             "path":             { "type": "string", "default": "." },
	             "docker_file":      { "type": "string" },
	             "quiet":            { "type": "boolean" },
	             "nocache":          { "type": "boolean" },
	             "rm":               { "type": "boolean" },
	             "timeout":          { "type": "number" },
	             "custom_context":   { "type": "boolean" },
	             "encoding":         { "type": "string" },
	             "pull":             { "type": "boolean" },
	             "forcerm":          { "type": "boolean" },
	             "buildargs":        { "type": "array" },
	             "decode":           { "type": "boolean" },
	             "shmsize":          { "type": "number" },
	             "labels":           { "type": "array" },
	             "container_limits": {
	               "type": "array",
	               "items": {
	                 "memory":     { "type": "number" },
	                 "memswap":    { "type": "number" },
	                 "cpushares":  { "type": "number" },
	                 "cpusetcpus": { "type": "string" }
	                }
	             },
	           },
	           "additionalProperties": False
	         },
	       },
	     }


# Setting global vars, initializing dicts
global cfg_file, cfg, logger, args, actions, docker_client
global access_key, secret_key, region, account_id, ecr_repo

actions={ 'build': False,
          'push': False,
          'push_to_ecr': False
        }
cfg={}


# Functions
def load_yaml( file ):
    try:
        with open(file, 'r') as yml_file:
             global cfg
             cfg = yaml.load(yml_file)
    except Exception as e:
           logger.fatal('Error loading yaml file config, it seems broken!'+ str(file))
           sys.exit(-1)

def chk_yml_file( file ):
    if os.path.exists( file ) and os.path.isfile( file ):
       return True
    return False

def cli_args_builder():
    parser = argparse.ArgumentParser(description=str(CONST.APP_NAME_HELP))
    parser.add_argument('--config', '-c', dest='cfg_file', metavar='FILE',
                        help='Optional YaML config file. by default .ecr_docker_ci.yml')
    return vars(parser.parse_args())

def cfg_builder():
    if args['cfg_file'] is None:
       cfg_file = os.path.join(os.getcwd(),CONST.DEFAULT_CONF_FILE)
    else:
       cfg_file = args['cfg_file']

    if not chk_yml_file( cfg_file ):
          logger.fatal('Config YaML file not found. Aborting')
          sys.exit(-1)
    load_yaml( cfg_file )
    try:
           validate(cfg,  global_sch)
    except ValidationError as e:
           logger.fatal('Fatal error validating YaML conf: '+str(e.message))
           sys.exit(-1)
    if 'build' in cfg['Global']['actions']:
       actions['build'] = True
    if 'push' in cfg['Global']['actions']:
       actions['push'] = True
    if 'push_to_ecr' in cfg['Global']['actions']:
       actions['push_to_ecr'] = True

def get_boto_client( **kwargs ):
    if kwargs is not None:
       if 'meth' not in kwargs.keys():
          logger.fatal('get_boto_client: method undefined!')
          sys.exit(-1)
       if 'aws_access_key_id' not in kwargs.keys():
          logger.fatal('get_boto_client: AWS ACCESS KEY ID undefined!')
          sys.exit(-1)
       if 'aws_secret_access_key' not in kwargs.keys():
          logger.fatal('get_boto_client: AWS SECRET ACCESS KEY undefined!')
          sys.exit(-1)
       if 'region_name' not in kwargs.keys():
          logger.fatal('get_boto_client: AWS region undefined!')
          sys.exit(-1)
       return boto3.client(
                            kwargs['meth'],
                            aws_access_key_id=kwargs['aws_access_key_id'],
                            aws_secret_access_key=kwargs['aws_secret_access_key'],
                            region_name=kwargs['region_name']
                          )

def get_aws_account_id():
    sts = get_boto_client( meth='sts',
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            region_name=region,
                         )
    try:
        user_arn = sts.get_caller_identity()["Arn"]
        account_id = user_arn.split(":")[4]
        logger.info('The AWS account id from your credentials is: '+ str(account_id))
        return account_id
    except Exception as e:
        logger.fatal(str(e.message))
        sys.exit(-1)

def auth_to_ecr( account_id ):
    client = get_boto_client( meth='ecr',
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            region_name=region,
                         )
    response = client.get_authorization_token(
        registryIds=[
             account_id,
        ]
    )
    if response:
       logger.info('Getting AWS token to docker login')

    auth_token = b64decode(response["authorizationData"][0]["authorizationToken"]).decode()
    username, password = auth_token.split(':')

    return { 'token'    : auth_token,
             'username' : username,
             'password' : password,
             'endpoint' : response["authorizationData"][0]["proxyEndpoint"]
           }

def initialize_docker_client():
    global docker_client
    try:
        try:
            docker_client = docker.DockerClient(base_url=cfg['Docker']['daemon'])
        except AttributeError:
            docker_client = docker.Client(base_url=cfg['Docker']['daemon'])
        del cfg['Docker']['daemon'] # Prevents Docker build args conflict
    except KeyError:
        docker_client = docker.from_env()

def docker_login( username, password, registry, reauth=True ):
    return docker_client.login( username=username,
                         password=password,
                         registry=registry,
                         reauth=reauth
                       )

def docker_login_to_ecr( auth_token ):
    docker_response =  docker_login( username=auth_token['username'],
                         password=auth_token['password'],
                         registry=auth_token['endpoint'],
                         reauth=True
                       )
    if re.match('^Login.*Succeeded$', str(docker_response['Status'])) is not None:
       logger.info('Login to AWS ECR Succeeded!')
       return True
    else:
       logger.info('Login to AWS ECR Failed!')
       return False

def docker_tag( image_source, image_final, tag ):
    return docker_client.tag(image_source, image_final, tag,
               force=True)

def docker_push( repository, tag='latest', insecure_registry=False, stream=True ):
    logger.info('Pushing Docker image with tag: '+repository)
    output={}
    for output_line in docker_client.push( repository=repository,
                             	    tag=tag,
                             	    insecure_registry=insecure_registry,
                             	    stream=stream
                           	  ):
        output.update(eval(output_line))
    logger.info(output['status'])

def docker_build( **kwargs ):
    try:
        kwargs['path']
    except KeyError:
        kwargs['path'] = '.'

    logger.info('Building Docker image with tag: '+str(kwargs['tag']))
    for output_line in docker_client.build( **kwargs ):
        logger.info(eval(output_line)['stream'].rstrip())



if __name__ == '__main__':

    CONST = _Const()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s -  %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    args = cli_args_builder()
    cfg_builder()
    initialize_docker_client()

    str_actions = ''
    for action, state in actions.iteritems():
        if state:
           str_actions = str_actions+' '+ action
    logger.info('Initializing '+ CONST.APP_NAME + ' with actions:' + str_actions)

    if actions['build']:
       try:
           validate(cfg, build_sch)
       except ValidationError as e:
           logger.fatal('Fatal error validating YaML conf: '+str(e.message))
           sys.exit(-1)
       logger.info('Starting action: "build"')
       docker_build(**cfg['Docker'])
    if actions['push']:
       try:
           validate(cfg, push_sch)
       except ValidationError as e:
           logger.fatal('Fatal error validating YaML conf: '+str(e.message))
           sys.exit(-1)
       logger.info('Starting action: "push"')
       local_img_tag = cfg['Docker']['tag'].split(':')
       docker_push( local_img_tag[0], local_img_tag[1] )
    if actions['push_to_ecr']:
       try:
           validate(cfg, aws_sch)
       except ValidationError as e:
           logger.fatal('Fatal error validating YaML conf: '+str(e.message))
           sys.exit(-1)

       logger.info('Starting action: "push_to_ecr"')
       access_key = cfg['Amazon ECR']['aws_access_key_id']
       secret_key = cfg['Amazon ECR']['aws_secret_access_key']
       region = cfg['Amazon ECR']['region_name']

       account_id = get_aws_account_id()
       auth_token = auth_to_ecr( account_id )
       if docker_login_to_ecr( auth_token ):
           local_img_tag = cfg['Docker']['tag'].split(':')
           image_final = str( account_id + '.dkr.ecr.' + region + '.amazonaws.com/'
                         + cfg['Amazon ECR']['ecr_repo_name'] )
           if docker_tag( cfg['Docker']['tag'], image_final, local_img_tag[1] ):
              docker_push( image_final, local_img_tag[1] )
       else:
           logger.fatal("Canno't login to ECR. Aborting")
           sys.exit(-1)
    logger.info("All it's done.")
    sys.exit(0)
