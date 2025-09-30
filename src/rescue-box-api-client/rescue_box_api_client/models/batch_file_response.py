from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.file_response import FileResponse


T = TypeVar("T", bound="BatchFileResponse")


@_attrs_define
class BatchFileResponse:
    """
    Attributes:
        files (list['FileResponse']):
        output_type (Union[Literal['batchfile'], None, Unset]):  Default: 'batchfile'.
    """

    files: list["FileResponse"]
    output_type: Union[Literal["batchfile"], None, Unset] = "batchfile"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        files = []
        for files_item_data in self.files:
            files_item = files_item_data.to_dict()
            files.append(files_item)

        output_type: Union[Literal["batchfile"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "files": files,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.file_response import FileResponse

        d = dict(src_dict)
        files = []
        _files = d.pop("files")
        for files_item_data in _files:
            files_item = FileResponse.from_dict(files_item_data)

            files.append(files_item)

        def _parse_output_type(data: object) -> Union[Literal["batchfile"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["batchfile"], data)
            if output_type_type_0 != "batchfile":
                raise ValueError(f"output_type_type_0 must match const 'batchfile', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["batchfile"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        batch_file_response = cls(
            files=files,
            output_type=output_type,
        )

        batch_file_response.additional_properties = d
        return batch_file_response

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
