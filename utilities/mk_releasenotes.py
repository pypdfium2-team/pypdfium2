# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import shutil
import subprocess
from os.path import dirname, abspath, join


SourceTree = dirname(dirname(abspath(__file__)))
Git = shutil.which('git')


def run_command(command, **kwargs):
    print(command)
    comp_process = subprocess.run(command, cwd=SourceTree, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kwargs)
    output = comp_process.stdout.decode('UTF-8').strip()
    return output


def _generate_tags_list():
    tags_str = run_command([Git, 'for-each-ref', '--sort=creatordate', '--format', '%(refname)', 'refs/tags'])
    tags_list = tags_str.split('\n')
    tags_list.reverse()
    return tags_list

TagsList = _generate_tags_list()


def get_tag(n_descends, skip_beta=False):
    
    for i, line in enumerate(TagsList):
        tag = line.split('/')[-1].strip()
        if skip_beta and 'b' in tag:
            continue
        if i >= n_descends:
            break
    
    return tag


def main():
    
    current_tag, prev_tag = get_tag(0), get_tag(1, True)
    print(current_tag, prev_tag)
    
    relnotes = "Release %s\n\n" % current_tag
    relnotes += "### Changes\n\nCommits between `%s` and `%s`:\n\n" % (prev_tag, current_tag)
    relnotes += run_command([Git, 'log', '%s..%s' % (prev_tag, current_tag), "--pretty=format:* %h %s"])
    relnotes += '\n'
    
    with open(join(SourceTree, 'RELEASE.md'), 'w') as fh:
        fh.write(relnotes)


if __name__ == '__main__':
    main()
