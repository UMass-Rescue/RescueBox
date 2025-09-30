from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.directory_response import DirectoryResponse


T = TypeVar("T", bound="BatchDirectoryResponse")


@_attrs_define
class BatchDirectoryResponse:
    """
    Attributes:
        directories (list['DirectoryResponse']):
        output_type (Union[Literal['batchdirectory'], None, Unset]):  Default: 'batchdirectory'.
    """

    directories: list["DirectoryResponse"]
    output_type: Union[Literal["batchdirectory"], None, Unset] = "batchdirectory"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        directories = []
        for directories_item_data in self.directories:
            directories_item = directories_item_data.to_dict()
            directories.append(directories_item)

        output_type: Union[Literal["batchdirectory"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "directories": directories,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.directory_response import DirectoryResponse

        d = dict(src_dict)
        directories = []
        _directories = d.pop("directories")
        for directories_item_data in _directories:
            directories_item = DirectoryResponse.from_dict(directories_item_data)

            directories.append(directories_item)

        def _parse_output_type(data: object) -> Union[Literal["batchdirectory"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["batchdirectory"], data)
            if output_type_type_0 != "batchdirectory":
                raise ValueError(f"output_type_type_0 must match const 'batchdirectory', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["batchdirectory"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        batch_directory_response = cls(
            directories=directories,
            output_type=output_type,
        )

        batch_directory_response.additional_properties = d
        return batch_directory_response

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
