# container-layer-check

This is an action to check if the specified container shares layers with the parent. If the parent layers do not match, the parent image has likely changed. This action performs the check without pulling the images, and works across repositories.

This action depends on `skopeo` and at least version 3.9 of `python`. It should work on any of the available Ubuntu runners from `ubunt-18.04` on.

## Example workflow

If you maintain the container `x`, pushed to repo `quay.io/x` and it is built from the `debian:stable-slim` parent (it has a `FROM debian:stable-slim` in the `Containerfile`/`Dockerfile`), you could set up a cron schedule to see if the parent has changed:

```yaml
on:
  schedule:
    - cron: '30 12 * * *'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - id: container-layer-check
        uses: timkent/container-layer-check@v1
        with:
          container: quay.io/x/x:latest
          parent: debian:stable-slim
      - uses: actions/checkout@v2
        if: steps.container-layer-check.outputs.match == 'false'
```

The `checkout` step has an `if` condition to ensure it only runs if the parent image layers do not match.

Keep in mind that this is just checking the container layers, so if as part of your build process you install extra packages, it won't be able to tell you if the packages need updating.

## Inputs

| Input       | Description              |
|-------------|--------------------------|
| `container` | Container image to check |
| `parent`    | Parent image to check    |

## Outputs

| Output  | Description                                              |
|---------|----------------------------------------------------------|
| `match` | Returns `true` if parent layers match, otherwise `false` |
