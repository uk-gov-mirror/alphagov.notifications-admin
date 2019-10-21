import pytest

from tests.conftest import SERVICE_ONE_ID, normalize_spaces


@pytest.mark.parametrize('extra_args, expected_headings_and_events', (
    ({}, [
        (
            '12 December',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 12:12pm '
                'Renamed this service from ‘Example service’ to ‘Real service’'
            ),
        ),
        (
            '11 November',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 12:12pm '
                'Revoked the ‘Bad key’ API key'
            ),
        ),
        (
            '11 November',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 11:11am '
                'Created an API key called ‘Bad key’'
            ),
        ),
        (
            '10 October',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 11:10am '
                'Created an API key called ‘Good key’ '
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 2:01am '
                'Created this service and called it ‘Example service’'
            ),
        ),
    ]),
    ({'selected': 'api'}, [
        (
            '11 November',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 12:12pm '
                'Revoked the ‘Bad key’ API key'
            ),
        ),
        (
            '11 November',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 11:11am '
                'Created an API key called ‘Bad key’'
            ),
        ),
        (
            '10 October',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 11:10am '
                'Created an API key called ‘Good key’'
            ),
        ),
    ]),
    ({'selected': 'service'}, [
        (
            '12 December',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 12:12pm '
                'Renamed this service from ‘Example service’ to ‘Real service’'
            ),
        ),
        (
            '10 October',
            (
                '6ce466d0-fd6a-11e5-82f5-e0accb9d11a6 2:01am '
                'Created this service and called it ‘Example service’'
            ),
        ),
    ]),
))
def test_history(
    client_request,
    mock_get_service_history,
    mock_get_users_by_service,
    extra_args,
    expected_headings_and_events,
):
    page = client_request.get('main.history', service_id=SERVICE_ONE_ID, **extra_args)

    assert page.select_one('h1').text == 'Audit events'

    headings = page.select('main h2.heading-small')
    events = page.select('main ul.bottom-gutter')

    assert len(headings) == len(events) == len(expected_headings_and_events)

    for index, expected in enumerate(expected_headings_and_events):
        assert (
            normalize_spaces(headings[index].text),
            normalize_spaces(events[index].text),
        ) == expected
