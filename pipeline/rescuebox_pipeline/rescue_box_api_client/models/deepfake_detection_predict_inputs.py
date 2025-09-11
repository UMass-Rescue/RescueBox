from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.directory_input import DirectoryInput


T = TypeVar("T", bound="DeepfakeDetectionPredictInputs")


@_attrs_define
class DeepfakeDetectionPredictInputs:
    """
    Attributes:
        input_dataset (DirectoryInput):
        output_file (DirectoryInput):
    """

    input_dataset: "DirectoryInput"
    output_file: "DirectoryInput"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_dataset = self.input_dataset.to_dict()

        output_file = self.output_file.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input_dataset": input_dataset,
                "output_file": output_file,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.directory_input import DirectoryInput

        d = dict(src_dict)
        input_dataset = DirectoryInput.from_dict(d.pop("input_dataset"))

        output_file = DirectoryInput.from_dict(d.pop("output_file"))

        deepfake_detection_predict_inputs = cls(
            input_dataset=input_dataset,
            output_file=output_file,
        )

        deepfake_detection_predict_inputs.additional_properties = d
        return deepfake_detection_predict_inputs

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
