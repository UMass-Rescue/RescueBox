from collections.abc import Mapping
from typing import Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DirectoryResponse")


@_attrs_define
class DirectoryResponse:
    """
    Attributes:
        path (str):
        title (str):
        output_type (Union[Literal['directory'], None, Unset]):  Default: 'directory'.
        subtitle (Union[None, Unset, str]):
    """

    path: str
    title: str
    output_type: Union[Literal["directory"], None, Unset] = "directory"
    subtitle: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        title = self.title

        output_type: Union[Literal["directory"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        subtitle: Union[None, Unset, str]
        if isinstance(self.subtitle, Unset):
            subtitle = UNSET
        else:
            subtitle = self.subtitle

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "title": title,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if subtitle is not UNSET:
            field_dict["subtitle"] = subtitle

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        title = d.pop("title")

        def _parse_output_type(data: object) -> Union[Literal["directory"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["directory"], data)
            if output_type_type_0 != "directory":
                raise ValueError(f"output_type_type_0 must match const 'directory', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["directory"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_subtitle(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subtitle = _parse_subtitle(d.pop("subtitle", UNSET))

        directory_response = cls(
            path=path,
            title=title,
            output_type=output_type,
            subtitle=subtitle,
        )

        directory_response.additional_properties = d
        return directory_response

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
