from collections.abc import Mapping
from typing import Any, Literal, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MarkdownResponse")


@_attrs_define
class MarkdownResponse:
    """
    Attributes:
        value (str):
        output_type (Union[Literal['markdown'], None, Unset]):  Default: 'markdown'.
        title (Union[None, Unset, str]):
        subtitle (Union[None, Unset, str]):
    """

    value: str
    output_type: Union[Literal["markdown"], None, Unset] = "markdown"
    title: Union[None, Unset, str] = UNSET
    subtitle: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = self.value

        output_type: Union[Literal["markdown"], None, Unset]
        if isinstance(self.output_type, Unset):
            output_type = UNSET
        else:
            output_type = self.output_type

        title: Union[None, Unset, str]
        if isinstance(self.title, Unset):
            title = UNSET
        else:
            title = self.title

        subtitle: Union[None, Unset, str]
        if isinstance(self.subtitle, Unset):
            subtitle = UNSET
        else:
            subtitle = self.subtitle

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "value": value,
            }
        )
        if output_type is not UNSET:
            field_dict["output_type"] = output_type
        if title is not UNSET:
            field_dict["title"] = title
        if subtitle is not UNSET:
            field_dict["subtitle"] = subtitle

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        value = d.pop("value")

        def _parse_output_type(data: object) -> Union[Literal["markdown"], None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            output_type_type_0 = cast(Literal["markdown"], data)
            if output_type_type_0 != "markdown":
                raise ValueError(f"output_type_type_0 must match const 'markdown', got '{output_type_type_0}'")
            return output_type_type_0
            return cast(Union[Literal["markdown"], None, Unset], data)

        output_type = _parse_output_type(d.pop("output_type", UNSET))

        def _parse_title(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        title = _parse_title(d.pop("title", UNSET))

        def _parse_subtitle(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        subtitle = _parse_subtitle(d.pop("subtitle", UNSET))

        markdown_response = cls(
            value=value,
            output_type=output_type,
            title=title,
            subtitle=subtitle,
        )

        markdown_response.additional_properties = d
        return markdown_response

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
