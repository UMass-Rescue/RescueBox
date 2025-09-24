from collections.abc import Mapping
from typing import Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.file_type import FileType
from ..types import UNSET, Unset

T = TypeVar("T", bound="FileResponse")


@_attrs_define
class FileResponse:
    """
    Attributes:
        file_type (FileType):
        path (str):
        output_type (Union[Literal['file'], None, Unset]):  Default: 'file'.
        title (Union[None, Unset, str]):
        subtitle (Union[None, Unset, str]):
    """

    file_type: FileType
    path: str
    output_type: Union[Literal["file"], None, Unset] = "file"
    title: Union[None, Unset, str] = UNSET
    subtitle: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        file_type = self.file_type.value

        path = self.path

        output_type: Union[Literal["file"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        title: Union[None, Unset, str]
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        subtitle: Union[None, Unset, str]
        if isinstance(self.subtitle, Unset):
            subtitle = UNSET
        else:
            subtitle = self.subtitle

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "file_type": file_type,
                "path": path,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if title is not UNSET:
            field_dict["title"] = title
        if subtitle is not UNSET:
            field_dict["subtitle"] = subtitle

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        file_type = FileType(d.pop("file_type"))

        path = d.pop("path")

        def _parse_output_type(data: object) -> Union[Literal["file"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["file"], data)
            if output_type_type_0 != "file":
                raise ValueError(f"output_type_type_0 must match const 'file', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["file"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_title(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_subtitle(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subtitle = _parse_subtitle(d.pop("subtitle", UNSET))

        file_response = cls(
            file_type=file_type,
            path=path,
            output_type=output_type,
            title=title,
            subtitle=subtitle,
        )

        file_response.additional_properties = d
        return file_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
