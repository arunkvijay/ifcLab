# Copyright (C) 2022 Arun K Vijay <hello@arunkvijay.com>

import argparse
import uuid
import subprocess
import os.path

parser = argparse.ArgumentParser(description='email id')
parser.add_argument('--email', required=True, help='enter email id')
parser.add_argument('--project', required=True, help='enter project name')
args = parser.parse_args()

email = args.email
project = args.project 

cust_dir = str(uuid.uuid5(uuid.NAMESPACE_X500, email))

home_dir = os.path.expanduser('~')
customers_dir = os.path.join(home_dir, 'work', 'flow', 'projects', cust_dir)

if not os.path.exists(customers_dir):
    os.mkdir(customers_dir)
    org_dir_list = ['library', 'org_config']
    org_dirs = list(map(lambda dir: os.path.join(customers_dir, dir), org_dir_list))
    for d in org_dirs:
        os.mkdir(d)

project_dir = os.path.join(customers_dir, project.replace(' ','_').lower())
if not os.path.exists(project_dir):
    os.mkdir(project_dir)
    dir_list = ['ifc', 'cad', 'processing', 'project_config', 'from_client', 'ifcjs', 'obj', 'qtos', 'scripts']
    dirs = list(map(lambda dir: os.path.join(project_dir, dir), dir_list))
    for d in dirs:
        os.mkdir(d)

