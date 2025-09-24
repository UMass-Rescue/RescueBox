from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.file_input import FileInput
    from ..models.text_input import TextInput


T = TypeVar("T", bound="UFDRInputs")


@_attrs_define
class UFDRInputs:
    """
    Attributes:
        ufdr_file (FileInput):
        mount_name (TextInput):
    """

    ufdr_file: "FileInput"
    mount_name: "TextInput"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ufdr_file = self.ufdr_file.to_dict()

        mount_name = self.mount_name.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ufdr_file": ufdr_file,
                "mount_name": mount_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_input import FileInput
        from ..models.text_input import TextInput

        d = dict(src_dict)
        ufdr_file = FileInput.from_dict(d.pop("ufdr_file"))

        mount_name = TextInput.from_dict(d.pop("mount_name"))

        ufdr_inputs = cls(
            ufdr_file=ufdr_file,
            mount_name=mount_name,
        )

        ufdr_inputs.additional_properties = d
        return ufdr_inputs

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
