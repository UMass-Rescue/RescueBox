from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AudioDirectory")


@_attrs_define
class AudioDirectory:
    """
    Attributes:
        path (str):
        file_extensions (Union[Unset, list[str]]):
    """

    path: str
    file_extensions: Union[Unset, list[str]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        path = self.path

        file_extensions: Union[Unset, list[str]] = UNSET
        if not isinstance(self.file_extensions, Unset):
            file_extensions = self.file_extensions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
            }
        )
        if file_extensions is not UNSET:
            field_dict["file_extensions"] = file_extensions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        path = d.pop("path")

        file_extensions = cast(list[str], d.pop("file_extensions", UNSET))

        audio_directory = cls(
            path=path,
            file_extensions=file_extensions,
        )

        audio_directory.additional_properties = d
        return audio_directory

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
