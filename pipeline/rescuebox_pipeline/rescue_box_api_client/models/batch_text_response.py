from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.text_response import TextResponse


T = TypeVar("T", bound="BatchTextResponse")


@_attrs_define
class BatchTextResponse:
    """
    Attributes:
        texts (list['TextResponse']):
        output_type (Union[Literal['batchtext'], None, Unset]):  Default: 'batchtext'.
    """

    texts: list["TextResponse"]
    output_type: Union[Literal["batchtext"], None, Unset] = "batchtext"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        texts = []
        for texts_item_data in self.texts:
            texts_item = texts_item_data.to_dict()
            texts.append(texts_item)

        output_type: Union[Literal["batchtext"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "texts": texts,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.text_response import TextResponse

        d = dict(src_dict)
        texts = []
        _texts = d.pop("texts")
        for texts_item_data in _texts:
            texts_item = TextResponse.from_dict(texts_item_data)

            texts.append(texts_item)

        def _parse_output_type(data: object) -> Union[Literal["batchtext"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["batchtext"], data)
            if output_type_type_0 != "batchtext":
                raise ValueError(f"output_type_type_0 must match const 'batchtext', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["batchtext"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        batch_text_response = cls(
            texts=texts,
            output_type=output_type,
        )

        batch_text_response.additional_properties = d
        return batch_text_response

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
