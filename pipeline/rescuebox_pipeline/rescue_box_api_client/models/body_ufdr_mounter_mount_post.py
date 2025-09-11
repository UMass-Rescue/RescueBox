from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.ufdr_inputs import UFDRInputs
    from ..models.ufdr_parameters import UFDRParameters


T = TypeVar("T", bound="BodyUfdrMounterMountPost")


@_attrs_define
class BodyUfdrMounterMountPost:
    """
    Attributes:
        inputs (UFDRInputs):
        parameters (UFDRParameters):
    """

    inputs: "UFDRInputs"
    parameters: "UFDRParameters"
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
        from ..models.ufdr_inputs import UFDRInputs
        from ..models.ufdr_parameters import UFDRParameters

        d = dict(src_dict)
        inputs = UFDRInputs.from_dict(d.pop("inputs"))

        parameters = UFDRParameters.from_dict(d.pop("parameters"))

        body_ufdr_mounter_mount_post = cls(
            inputs=inputs,
            parameters=parameters,
        )

        body_ufdr_mounter_mount_post.additional_properties = d
        return body_ufdr_mounter_mount_post

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
