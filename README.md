# QVAC for Conda

Run AI models locally with [`tetherto-qvac-sdk`](https://pypi.org/project/tetherto-qvac-sdk/),
the Python SDK for [QVAC](https://github.com/tetherto/qvac). These Conda packages
include the QVAC worker and Bare runtime, so you can get started without a
separate Node.js installation.

## Install

With Pixi, create a project and add the SDK:

```sh
pixi init my-qvac-project
cd my-qvac-project
pixi workspace channel add https://prefix.dev/gbionics/qvac-prebuilt
pixi add tetherto-qvac-sdk
```
