"""CLI - Exceptions."""
from __future__ import absolute_import, print_function, unicode_literals

import contextlib
import sys

import click
import six

from ..core.api.exceptions import ApiException


@contextlib.contextmanager
def handle_api_exceptions(
        ctx, opts, context_msg=None, nl=False,
        exit_on_error=True, reraise_on_error=False):
    """Context manager that handles API exceptions."""
    # flake8: ignore=C901
    try:
        yield
    except ApiException as exc:
        if nl:
            click.echo()
            click.secho('ERROR: ', fg='red', nl=False)
        else:
            click.secho('ERROR', fg='red')

        context_msg = context_msg or 'Failed to perform operation!'
        click.secho(
            '%(context)s (status: %(code)s - %(code_text)s)' % {
                'context': context_msg,
                'code': exc.status,
                'code_text': exc.status_description
            }, fg='red'
        )

        if exc.detail:
            click.echo()
            click.secho(
                'Reason: %(detail)s' % {
                    'detail': exc.detail
                }, bold=True
            )

        if exc.fields:
            if not exc.detail:
                click.echo()

            for k, v in six.iteritems(exc.fields):
                if k == 'non_field_errors':
                    k = 'Validation'
                click.secho(
                    '%(field)s: %(message)s' % {
                        'field': click.style(k, bold=True),
                        'message': click.style(' '.join(v), fg='red')
                    }
                )

        hint = get_error_hint(ctx, opts, exc)
        if hint:
            click.secho(
                'Hint: %(hint)s' % {
                    'hint': click.style(hint, fg='yellow')
                }
            )

        if opts.verbose and not opts.debug:
            if exc.headers:
                click.echo()
                click.echo('Headers in Reply:')
                for k, v in six.iteritems(exc.headers):
                    click.echo(
                        '%(key)s = %(value)s' % {
                            'key': k,
                            'value': v
                        }
                    )

        if reraise_on_error:
            six.reraise(*sys.exc_info())

        if exit_on_error:
            ctx.exit(exc.status)


def get_error_hint(ctx, opts, exc):
    """Get a hint to show to the user (if any)."""
    module = sys.modules[__name__]
    get_specific_error_hint = (
        getattr(module, 'get_%s_error_hint' % exc.status, None))
    if get_specific_error_hint:
        return get_specific_error_hint(ctx, opts, exc)
    return None


def get_401_error_hint(ctx, opts, exc):
    """Get the hint for a 401/Unauthorised error."""
    # pylint: disable=unused-argument
    if opts.api_key:
        return (
            'Since you have an API key set, this probably means '
            'you don\'t have the permision to perform this action.')
    return (
        'You don\'t have an API key set, but it seems this action '
        'requires authenticated - Try getting your API key via '
        '`cloudsmith token` first then try again.')


def get_404_error_hint(ctx, opts, exc):
    """Get the hint for a 404/NotFound error."""
    # pylint: disable=unused-argument
    # pylint: disable=fixme
    # TODO(ls): Expand this to be contextual (we could look at the
    # arguments for the command).
    return 'This usually means the user/org is wrong or not visible.'


def get_500_error_hint(ctx, opts, exc):
    """Get the hint for a 500/InternalServerError error."""
    # pylint: disable=unused-argument
    return (
        'This usually means the Cloudsmith service is encountering '
        'issues, either with this specific command or as a whole. '
        'Please accept our apologies and try again later.'
    )
