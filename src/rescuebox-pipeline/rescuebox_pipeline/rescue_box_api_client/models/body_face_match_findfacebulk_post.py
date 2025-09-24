from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.find_face_bulk_inputs import FindFaceBulkInputs
    from ..models.find_face_bulk_parameters import FindFaceBulkParameters


T = TypeVar("T", bound="BodyFaceMatchFindfacebulkPost")


@_attrs_define
class BodyFaceMatchFindfacebulkPost:
    """
    Attributes:
        inputs (FindFaceBulkInputs):
        parameters (FindFaceBulkParameters):
    """

    inputs: "FindFaceBulkInputs"
    parameters: "FindFaceBulkParameters"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        inputs = self.inputs.to_dict()

        parameters = self.parameters.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "inputs": inputs,
                "parameters": parameters,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.find_face_bulk_inputs import FindFaceBulkInputs
        from ..models.find_face_bulk_parameters import FindFaceBulkParameters

        d = dict(src_dict)
        inputs = FindFaceBulkInputs.from_dict(d.pop("inputs"))

        parameters = FindFaceBulkParameters.from_dict(d.pop("parameters"))

        body_face_match_findfacebulk_post = cls(
            inputs=inputs,
            parameters=parameters,
        )

        body_face_match_findfacebulk_post.additional_properties = d
        return body_face_match_findfacebulk_post

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
