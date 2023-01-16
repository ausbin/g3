#!/usr/bin/env python3

import subprocess
import argparse
import os
import sys

def get_bucket_name():
    bucket = os.environ.get('G3_BUCKET', None)
    if not bucket:
        raise ValueError('please set $G3_BUCKET')
    return bucket

def parent_git_repo():
    cur_dir = os.getcwd()
    repo_path = cur_dir
    top_level = False
    while repo_path != '/' and not (top_level := os.path.isdir(os.path.join(repo_path, '.git'))):
        repo_path = os.path.normpath(os.path.join(repo_path, '..'))

    if not top_level:
        raise ValueError('this is not a directory tracked in git, giving up')

    _, repo_name = os.path.split(repo_path)
    # TODO: check name of remote matches repo_name

    relpath = os.path.relpath(cur_dir, repo_path)
    if relpath == '.':
        relpath == ''

    return repo_path, repo_name, relpath

def rclone_push(bucket, repo_name, relpath):
    subprocess.run(['rclone', 'sync', '--progress', '--checksum',
                    '--exclude={.gitignore,.g3}', '.', f's3:{bucket}/{repo_name}/{relpath}'], check=True)

def init_cmd(args):
    bucket = get_bucket_name()
    repo_path, repo_name, relpath = parent_git_repo()

    if subprocess.run(['git', 'diff', '--cached', '--quiet']).returncode:
        raise ValueError('something is in the staging area, bailing out')

    with open('.g3', 'x'):
        # Create empty file
        pass

    with open('.gitignore', 'x') as fp:
        fp.write('*\n' +
                 '!.gitignore\n' +
                 '!.g3\n')

    rclone_push(bucket, repo_name, relpath)

    subprocess.run(['git', 'add', '.g3', '.gitignore'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Add .g3 at /{relpath}/\n'], check=True)

    print("\nCommit created! Now `git push'!")

def push_cmd(args):
    bucket = get_bucket_name()

    if not os.path.isfile('.g3'):
        raise ValueError('this is not a directory tracked with g3, giving up')

    repo_path, repo_name, relpath = parent_git_repo()
    rclone_push(bucket, repo_name, relpath)

def main(argv):
    parser = argparse.ArgumentParser(prog='g3')
    subparsers = parser.add_subparsers(help='sub-commands:', required=True)

    init_parser = subparsers.add_parser('init', help='start syncing this directory with g3')
    init_parser.set_defaults(func=init_cmd)

    push_parser = subparsers.add_parser('push', help='push to s3')
    push_parser.set_defaults(func=push_cmd)

    args = parser.parse_args(argv)
    args.func(args)

if __name__ == '__main__':
    main(sys.argv[1:])
