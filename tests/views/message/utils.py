import time

import shortuuid

from django_unicorn.utils import generate_checksum


def post_and_get_response(
    client,
    *,
    url="",
    data=None,
    action_queue=None,
    component_id=None,
    hash=None,  # noqa: A002
    return_response=False,
):
    if not data:
        data = {}
    if not action_queue:
        action_queue = []
    if not component_id:
        component_id = shortuuid.uuid()[:8]

    data_checksum = generate_checksum(data)
    meta = f"{data_checksum}:{hash or ''}:{time.time()}"

    message = {
        "actionQueue": action_queue,
        "data": data,
        "meta": meta,
        "id": component_id,
        "epoch": time.time(),
    }

    response = client.post(
        url,
        message,
        content_type="application/json",
    )

    if return_response:
        return response

    try:
        return response.json()
    except TypeError:
        # Return the regular response if no JSON for HttpResponseNotModified
        return response
