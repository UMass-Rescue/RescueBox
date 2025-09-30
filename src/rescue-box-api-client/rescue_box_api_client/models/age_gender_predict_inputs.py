from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.directory_input import DirectoryInput


T = TypeVar("T", bound="AgeGenderPredictInputs")


@_attrs_define
class AgeGenderPredictInputs:
    """
    Attributes:
        image_directory (DirectoryInput):
    """

    image_directory: "DirectoryInput"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        image_directory = self.image_directory.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "image_directory": image_directory,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.directory_input import DirectoryInput

        d = dict(src_dict)
        image_directory = DirectoryInput.from_dict(d.pop("image_directory"))

        age_gender_predict_inputs = cls(
            image_directory=image_directory,
        )

        age_gender_predict_inputs.additional_properties = d
        return age_gender_predict_inputs

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
