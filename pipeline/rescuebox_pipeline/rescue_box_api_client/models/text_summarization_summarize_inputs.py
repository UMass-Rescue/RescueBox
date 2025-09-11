from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.directory_input import DirectoryInput


T = TypeVar("T", bound="TextSummarizationSummarizeInputs")


@_attrs_define
class TextSummarizationSummarizeInputs:
    """
    Attributes:
        input_dir (DirectoryInput):
        output_dir (DirectoryInput):
    """

    input_dir: "DirectoryInput"
    output_dir: "DirectoryInput"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        input_dir = self.input_dir.to_dict()

        output_dir = self.output_dir.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input_dir": input_dir,
                "output_dir": output_dir,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.directory_input import DirectoryInput

        d = dict(src_dict)
        input_dir = DirectoryInput.from_dict(d.pop("input_dir"))

        output_dir = DirectoryInput.from_dict(d.pop("output_dir"))

        text_summarization_summarize_inputs = cls(
            input_dir=input_dir,
            output_dir=output_dir,
        )

        text_summarization_summarize_inputs.additional_properties = d
        return text_summarization_summarize_inputs

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
