# Release Notes

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

**Note:** Until 1.0 any MAJOR or MINOR release may have backwards-incompatible changes.

## [Unreleased]

- **Added** configuration profiles, to support multiple environments.
- **Added** `api_host`, `api_proxy` and `api_user_agent` to config file.
- **Added** `help` command for those who need more than `-h` and `--help`.
- **Added** service endpoint to `check` command output.
- **Added** ability to upload multiple package files at once.
- **Added* tox-based testing for Python2.x and Python3.x.
- **Changed** environment variables to use a `CLOUDSMITH_` prefix.
- **Fixed** validation for `push` commands that require a distribution.
- **Fixed** token endpoint failing because API key overrides login/password.
- **Fixed* Python3 compatibility.

## [0.1.0] - 2017-11-23

- Initial release.