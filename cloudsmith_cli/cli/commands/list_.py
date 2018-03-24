"""CLI/Commands - List objects."""
from __future__ import absolute_import, print_function, unicode_literals

from operator import itemgetter

import click
from click_spinner import spinner
import json

from . import main
from .. import command, decorators, utils, validators
from ...core.api.distros import list_distros
from ...core.api.packages import (
    get_package_format_names_with_distros, list_packages
)
from ...core.api.repos import list_repos
from ..exceptions import handle_api_exceptions


@main.group(cls=command.AliasGroup, name='list', aliases=['ls'])
@decorators.common_cli_config_options
@decorators.common_cli_output_options
@decorators.common_api_auth_options
@decorators.initialise_api
@click.pass_context
def list_(ctx, opts):  # pylint: disable=unused-argument
    """List distributions, packages and repos."""


@list_.command()
@decorators.common_cli_config_options
@decorators.common_cli_output_options
@decorators.common_api_auth_options
@decorators.initialise_api
@click.argument(
    'package-format', default=None, required=False,
    type=click.Choice(get_package_format_names_with_distros()))
@click.pass_context
def distros(ctx, opts, package_format):
    """List available distributions."""
    # Use stderr for messages if the output is something else (e.g.  # JSON)
    use_stderr =  opts.output != 'pretty'

    click.echo(
        'Getting list of distributions ... ', nl=False, err=use_stderr
    )

    context_msg = 'Failed to get list of distributions!'
    with handle_api_exceptions(ctx, opts=opts, context_msg=context_msg):
        with spinner():
            distros_ = list_distros(package_format=package_format)

    click.secho('OK', fg='green', err=use_stderr)

    if maybe_print_as_json(opts, distros_):
        return

    headers = ['Distro', 'Release', 'Format', 'Distro / Release (Identifier)']
    if package_format:
        headers.remove('Format')

    rows = []
    for distro in sorted(distros_, key=itemgetter('slug')):
        if not distro['versions']:
            continue

        for release in sorted(distro['versions'], key=itemgetter('slug')):
            row = [
                click.style(distro['name'], fg='cyan'),
                click.style(release['name'], fg='yellow'),
                click.style(distro['format'], fg='blue'),
                '%(distro)s/%(release)s' % {
                    'distro': click.style(distro['slug'], fg='green'),
                    'release': click.style(release['slug'], fg='magenta')
                }
            ]

            if package_format:
                row.pop(2)  # Remove format column

            rows.append(row)

    if distros_:
        click.echo()
        utils.pretty_print_table(headers, rows)

    click.echo()

    num_results = sum(
        1 for distro in distros_ for release in distro['versions'] if release
    )
    list_suffix = 'distribution release%s' % ('s' if num_results != 1 else '')
    utils.pretty_print_list_info(num_results=num_results, suffix=list_suffix)


@list_.command()
@decorators.common_cli_config_options
@decorators.common_cli_output_options
@decorators.common_cli_list_options
@decorators.common_api_auth_options
@decorators.initialise_api
@click.argument(
    'owner_repo', metavar='OWNER/REPO',
    callback=validators.validate_owner_repo)
@click.option(
    '-q', '--query',
    help=(
        'A boolean-like search term for querying package attributes.'
    )
)
@click.pass_context
def packages(ctx, opts, owner_repo, page=None, page_size=None, query=None):
    """
    List packages for a repository.

    OWNER/REPO: Specify the OWNER namespace (i.e. user or org), and the
    REPO name to list packages for that namespace and repository. All separated
    by a slash.

    You can use the search query (-q|--query) to filter packages:

      - By name: 'my-package' (implicit) or 'name:my-package'

      - By filename: 'pkg.ext' (implicit) or 'filename:pkg.ext' (explicit)

      - By version: '1.0.0' (implicit) or 'version:1.0.0' (explicit)

      - By arch: 'x86_64' (implicit) or 'architecture:x86_64' (explicit)

      - By disto: 'el' (implicit) or 'distribution:el' (explicit)

    You can also modify the search terms:

      - '^foo' to anchor to start of term

      - 'foo$' to anchor to end of term

      - 'foo*bar' for fuzzy matching

      - '~foo' for negation of the term (explicit only, e.g. name:~foo)

    Multiple search terms are conjunctive (AND).

    Examples, to find packages named exactly foo, with a zip filename, that are
    NOT the x86 architecture, use something like this:

    --query 'name:^foo$ filename:.zip$ architecture:~x86'
    """
    owner, repo = owner_repo

    # Use stderr for messages if the output is something else (e.g.  # JSON)
    use_stderr =  opts.output != 'pretty'

    click.echo(
        'Getting list of packages ... ', nl=False, err=use_stderr
    )

    context_msg = 'Failed to get list of packages!'
    with handle_api_exceptions(ctx, opts=opts, context_msg=context_msg):
        with spinner():
            packages_, page_info = list_packages(
                owner=owner, repo=repo, page=page, page_size=page_size,
                query=query
            )

    click.secho('OK', fg='green', err=use_stderr)

    if maybe_print_as_json(opts, packages_, page_info):
        return

    headers = ['Name', 'Version', 'Status', 'Owner / Repository (Identifier)']
    rows = []
    for package in sorted(packages_, key=itemgetter('slug')):
        rows.append([
            click.style(_get_package_name(package), fg='cyan'),
            click.style(_get_package_version(package), fg='yellow'),
            click.style(_get_package_status(package), fg='blue'),
            '%(owner_slug)s/%(repo_slug)s/%(slug)s' % {
                'owner_slug': click.style(package['namespace'], fg='green'),
                'repo_slug': click.style(package['repository'], fg='green'),
                'slug': click.style(package['slug'], fg='magenta'),
            }
        ])

    if packages_:
        click.echo()
        utils.pretty_print_table(headers, rows)

    click.echo()

    num_results = len(packages_)
    list_suffix = 'package%s visible' % ('s' if num_results != 1 else '')
    utils.pretty_print_list_info(
        num_results=num_results, page_info=page_info, suffix=list_suffix
    )


@list_.command()
@decorators.common_cli_config_options
@decorators.common_cli_output_options
@decorators.common_cli_list_options
@decorators.common_api_auth_options
@decorators.initialise_api
@click.argument(
    'owner', default=None, required=False)
@click.pass_context
def repos(ctx, opts, owner, page=None, page_size=None):
    """
    List repositories for a namespace (owner).

    OWNER: Specify the OWNER namespace (i.e. user or org) to list the
    repositories for that namespace.

    If OWNER isn't specified it'll default to the currently authenticated user
    (if any). If you're unauthenticated, no results will be returned.
    """
    # Use stderr for messages if the output is something else (e.g.  # JSON)
    use_stderr =  opts.output != 'pretty'

    click.echo(
        'Getting list of repositories ... ', nl=False, err=use_stderr
    )

    context_msg = 'Failed to get list of repositories!'
    with handle_api_exceptions(ctx, opts=opts, context_msg=context_msg):
        with spinner():
            repos_, page_info = list_repos(
                owner=owner, page=page, page_size=page_size
            )

    click.secho('OK', fg='green', err=use_stderr)

    if maybe_print_as_json(opts, repos_, page_info):
        return

    headers = ['Name', 'Type', 'Owner / Repository (Identifier)']

    rows = []
    for repo in sorted(repos_, key=itemgetter('slug')):
        rows.append([
            click.style(repo['name'], fg='cyan'),
            click.style(repo['repository_type_str'], fg='yellow'),
            '%(owner_slug)s/%(slug)s' % {
                'owner_slug': click.style(repo['namespace'], fg='green'),
                'slug': click.style(repo['slug'], fg='magenta'),
            }
        ])

    if repos_:
        click.echo()
        utils.pretty_print_table(headers, rows)

    click.echo()

    num_results = len(repos_)
    list_suffix = 'repositor%s visible' % ('ies' if num_results != 1 else 'y')
    utils.pretty_print_list_info(
        num_results=num_results, page_info=page_info, suffix=list_suffix
    )


def _get_package_name(package):
    """Get the name (or filename) for a package."""
    return package['name'] or package['filename']


def _get_package_status(package):
    """Get the status for a package."""
    status = package['status_str'] or 'Unknown'
    stage = package['stage_str'] or 'Unknown'
    if stage == 'Fully Synchronised':
        return status
    return '%(status)s / %(stage)s' % {
        'status': status,
        'stage': stage
    }


def _get_package_version(package):
    """Get the version for a package (if any)."""
    return package['version'] or 'None'


def maybe_print_as_json(opts, data, page_info=None):
    if not opts.output in ('json', 'pretty_json'):
        return False

    full_data = {'results': data}

    if page_info is not None and page_info.is_valid:
        full_data['_pagination'] = page_info.as_dict(num_results=len(data))

    if opts.output == 'pretty_json':
        full_data = json.dumps(full_data, indent=4, sort_keys=True)

    click.echo(full_data)
    return True
