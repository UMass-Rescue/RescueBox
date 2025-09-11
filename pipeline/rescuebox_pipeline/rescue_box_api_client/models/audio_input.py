from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.audio_directory import AudioDirectory


T = TypeVar("T", bound="AudioInput")


@_attrs_define
class AudioInput:
    """
    Attributes:
        input_dir (AudioDirectory):
    """

    input_dir: "AudioDirectory"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_dir = self.input_dir.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input_dir": input_dir,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.audio_directory import AudioDirectory

        d = dict(src_dict)
        input_dir = AudioDirectory.from_dict(d.pop("input_dir"))

        audio_input = cls(
            input_dir=input_dir,
        )

        audio_input.additional_properties = d
        return audio_input

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
