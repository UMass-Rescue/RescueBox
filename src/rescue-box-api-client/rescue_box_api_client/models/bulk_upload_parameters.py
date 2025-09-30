from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="BulkUploadParameters")


@_attrs_define
class BulkUploadParameters:
    """
    Attributes:
        dropdown_collection_name (str):
        collection_name (str):
    """

    dropdown_collection_name: str
    collection_name: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        dropdown_collection_name = self.dropdown_collection_name

        collection_name = self.collection_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "dropdown_collection_name": dropdown_collection_name,
                "collection_name": collection_name,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        dropdown_collection_name = d.pop("dropdown_collection_name")

        collection_name = d.pop("collection_name")

        bulk_upload_parameters = cls(
            dropdown_collection_name=dropdown_collection_name,
            collection_name=collection_name,
        )

        bulk_upload_parameters.additional_properties = d
        return bulk_upload_parameters

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
