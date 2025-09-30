from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.batch_directory_response import BatchDirectoryResponse
from ...models.batch_file_response import BatchFileResponse
from ...models.batch_text_response import BatchTextResponse
from ...models.body_face_match_deletecollection_post import BodyFaceMatchDeletecollectionPost
from ...models.directory_response import DirectoryResponse
from ...models.file_response import FileResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.markdown_response import MarkdownResponse
from ...models.text_response import TextResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    body: BodyFaceMatchDeletecollectionPost,
    streaming: Union[None, Unset, bool] = False,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    params: dict[str, Any] = {}

    json_streaming: Union[None, Unset, bool]
    if isinstance(streaming, Unset):
        json_streaming = UNSET
    else:
        json_streaming = streaming
    params["streaming"] = json_streaming

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/face-match/deletecollection",
        "params": params,
    }

    _body = body.to_dict()

    _kwargs["json"] = _body
    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    if response.status_code == 200:

        def _parse_response_200(
            data: object,
        ) -> Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_0 = FileResponse.from_dict(data)

                return componentsschemas_response_body_type_0
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_1 = DirectoryResponse.from_dict(data)

                return componentsschemas_response_body_type_1
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_2 = MarkdownResponse.from_dict(data)

                return componentsschemas_response_body_type_2
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_3 = TextResponse.from_dict(data)

                return componentsschemas_response_body_type_3
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_4 = BatchFileResponse.from_dict(data)

                return componentsschemas_response_body_type_4
            except:  # noqa: E722
                pass
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_response_body_type_5 = BatchTextResponse.from_dict(data)

                return componentsschemas_response_body_type_5
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            componentsschemas_response_body_type_6 = BatchDirectoryResponse.from_dict(data)

            return componentsschemas_response_body_type_6

        response_200 = _parse_response_200(response.json())

        return response_200
    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: BodyFaceMatchDeletecollectionPost,
    streaming: Union[None, Unset, bool] = False,
) -> Response[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    """/Face-Match/Deletecollection

    Args:
        streaming (Union[None, Unset, bool]):  Default: False.
        body (BodyFaceMatchDeletecollectionPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['BatchDirectoryResponse', 'BatchFileResponse', 'BatchTextResponse', 'DirectoryResponse', 'FileResponse', 'MarkdownResponse', 'TextResponse']]]
    """

    kwargs = _get_kwargs(
        body=body,
        streaming=streaming,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: BodyFaceMatchDeletecollectionPost,
    streaming: Union[None, Unset, bool] = False,
) -> Optional[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    """/Face-Match/Deletecollection

    Args:
        streaming (Union[None, Unset, bool]):  Default: False.
        body (BodyFaceMatchDeletecollectionPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['BatchDirectoryResponse', 'BatchFileResponse', 'BatchTextResponse', 'DirectoryResponse', 'FileResponse', 'MarkdownResponse', 'TextResponse']]
    """

    return sync_detailed(
        client=client,
        body=body,
        streaming=streaming,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: BodyFaceMatchDeletecollectionPost,
    streaming: Union[None, Unset, bool] = False,
) -> Response[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    """/Face-Match/Deletecollection

    Args:
        streaming (Union[None, Unset, bool]):  Default: False.
        body (BodyFaceMatchDeletecollectionPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, Union['BatchDirectoryResponse', 'BatchFileResponse', 'BatchTextResponse', 'DirectoryResponse', 'FileResponse', 'MarkdownResponse', 'TextResponse']]]
    """

    kwargs = _get_kwargs(
        body=body,
        streaming=streaming,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: BodyFaceMatchDeletecollectionPost,
    streaming: Union[None, Unset, bool] = False,
) -> Optional[
    Union[
        HTTPValidationError,
        Union[
            "BatchDirectoryResponse",
            "BatchFileResponse",
            "BatchTextResponse",
            "DirectoryResponse",
            "FileResponse",
            "MarkdownResponse",
            "TextResponse",
        ],
    ]
]:
    """/Face-Match/Deletecollection

    Args:
        streaming (Union[None, Unset, bool]):  Default: False.
        body (BodyFaceMatchDeletecollectionPost):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, Union['BatchDirectoryResponse', 'BatchFileResponse', 'BatchTextResponse', 'DirectoryResponse', 'FileResponse', 'MarkdownResponse', 'TextResponse']]
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            streaming=streaming,
        )
    ).parsed
