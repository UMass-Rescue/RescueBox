from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validation_error import ValidationError


T = TypeVar("T", bound="HTTPValidationError")


@_attrs_define
class HTTPValidationError:
    """
    Attributes:
        detail (Union[Unset, list['ValidationError']]):
    """

    detail: Union[Unset, list["ValidationError"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        detail: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.detail, Unset):
            detail = []
            for detail_item_data in self.detail:
                detail_item = detail_item_data.to_dict()
                detail.append(detail_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if detail is not UNSET:
            field_dict["detail"] = detail

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validation_error import ValidationError

        d = dict(src_dict)
        detail = []
        _detail = d.pop("detail", UNSET)
        if isinstance(_detail, list):
            for detail_item_data in _detail or []:
                if isinstance(detail_item_data, dict):
                    detail_item = ValidationError.from_dict(detail_item_data)
                    detail.append(detail_item)
                elif isinstance(detail_item_data, str):
                    # Handle case where detail item is a simple string
                    detail_item = ValidationError(loc=[], msg=detail_item_data, type_="string_error")
                    detail.append(detail_item)
        elif isinstance(_detail, str):
            # Handle case where detail is a simple string
            detail_item = ValidationError(loc=[], msg=_detail, type_="string_error")
            detail.append(detail_item)

        http_validation_error = cls(
            detail=detail,
        )

        http_validation_error.additional_properties = d
        return http_validation_error

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
