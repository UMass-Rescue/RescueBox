from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.bulk_upload_inputs import BulkUploadInputs
    from ..models.bulk_upload_parameters import BulkUploadParameters


T = TypeVar("T", bound="BodyFaceMatchBulkuploadPost")


@_attrs_define
class BodyFaceMatchBulkuploadPost:
    """
    Attributes:
        inputs (BulkUploadInputs):
        parameters (BulkUploadParameters):
    """

    inputs: "BulkUploadInputs"
    parameters: "BulkUploadParameters"
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
        from ..models.bulk_upload_inputs import BulkUploadInputs
        from ..models.bulk_upload_parameters import BulkUploadParameters

        d = dict(src_dict)
        inputs = BulkUploadInputs.from_dict(d.pop("inputs"))

        parameters = BulkUploadParameters.from_dict(d.pop("parameters"))

        body_face_match_bulkupload_post = cls(
            inputs=inputs,
            parameters=parameters,
        )

        body_face_match_bulkupload_post.additional_properties = d
        return body_face_match_bulkupload_post

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
