#!/usr/bin/env python

import functools
import json
import os
import subprocess
import sys

from urllib.parse import urlparse


class Container:
    def __init__(self, image: str):
        self.image = self._normalise_image_name(image)
        pass

    @functools.cached_property
    def config(self) -> dict:
        try:
            skopeo = subprocess.run(['skopeo', 'inspect', '--config', self.image],
                                    capture_output=True, check=True, text=True)
        except subprocess.CalledProcessError as e:
            print(f'::error title=skopeo::{e.stderr}')
            sys.exit(e.returncode)
        return json.loads(skopeo.stdout)

    @functools.cached_property
    def layers(self) -> list:
        return self.config['rootfs']['diff_ids']

    @staticmethod
    def _normalise_image_name(image: str) -> str:
        # Return if non-docker format
        # https://github.com/containers/skopeo/blob/main/docs/skopeo.1.md
        other_formats = ('containers-storage:', 'dir:', 'docker-archive:', 'docker-daemon:', 'oci:', 'oci-archive:')
        if image.startswith(other_formats):
            return image

        # Enforce docker scheme (workaround for urlparse() being confused by ':' in tag specifier)
        image = image.removeprefix('docker:')
        if not image.startswith('//'):
            if image.count('/') > 1:
                image = f'//{image}'
        url = urlparse(f'docker:{image}')

        # Default to docker.io
        if not url.netloc:
            url = url._replace(netloc='docker.io')
        path, _, tag = url.path.partition(':')
        path = path.removeprefix('/')

        # Handle official images
        if url.netloc == 'docker.io' and '/' not in path:
            path = f'library/{path}'

        if tag:
            return f'{url._replace(path=path).geturl()}:{tag}'
        return url._replace(path=path).geturl()


if __name__ == '__main__':
    container = Container(os.environ['CONTAINER'].strip())
    parent = Container(os.environ['PARENT'].strip())

    print(f'Checking if "{container.image}" shares a layer with "{parent.image}"')
    if any(layer in container.layers for layer in parent.layers):
        print('Matching layer found')
        match = 'true'
    else:
        print('No match was found')
        match = 'false'

    print(f'Setting "match" to "{match}"')
    print(f'::set-output name=match::{match}')
