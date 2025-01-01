from pathlib import Path
import json
from types import NoneType
from typing import Any, Generator
import xml.etree.ElementTree as ET

from frozendict import frozendict

from backend.project.config import DocLabel
from backend.utils.functions import flatten_lists
from backend.utils.nlp import SpacyModel


def file_to_doc(file_path: Path) -> dict | list:
    """Converts files to a dictionary/list representation."""
    ext = file_path.suffix
    if ext == ".json":
        return json.load(file_path.open())
    elif ext == ".xml":
        return xml_to_dict(file_path)
    raise NotImplementedError(f"No support for extension {ext} yet.")


def xml_to_dict(file_path: Path) -> dict:
    """
    Converts an XML file to a dictionary with frozendict as keys containing
    the tag and its attributes.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()
    return xml_to_dict_inner(root)  # type: ignore


def xml_to_dict_inner(node: ET.Element) -> dict | list:
    # Create a frozendict for the current node containing the tag and attributes
    current_node = frozendict({"_tag": node.tag}, **node.attrib)

    # If the node has children, recursively process them
    children = [xml_to_dict_inner(child) for child in node]

    # Create the dictionary entry
    if children:
        return {current_node: children}
    else:
        node_text = node.text.strip() if node.text else None
        return {current_node: node_text}


def get_content_under_doc_labels(
    doc_section: Any,
    target_doc_labels: list[DocLabel],
    target_parent_label_names: set[str] | None = None,
) -> Generator[dict[str, Any | set[str]], None, None]:
    """
    (See DocLabel.match_label documentation for how DocLabels correspond
    to keys in doc_section.)

    Iterator of:
        - terminal content under keys corresponding to provided DocLabels
        - names of those ancestor keys/DocLabels

    Example:

    doc_section = [
        "label_1" : {
            "label_2: : [
                "string 1",
                "string 2",
            ],
            "label_3" : " string 3",
        },
    ]

    target_doc_labels = [<DocLabel for "label_1">, <DocLabel for "label_2">]

    Yields:
        ("string1", { <DocLabel for "label_1">.name, <DocLabel for "label_2">.name })
        ("string2", { <DocLabel for "label_1">.name, <DocLabel for "label_2">.name })
        ("string3", { <DocLabel for "label_1">.name,)


    Args:
        doc_section (Any): Section of document
        target_doc_labels (list[DocLabel]): DocLabels corresponding to keys
            containing relevant text content
        target_label_parent_refs (set[str]): list of DocLabel names.

    Yields:
        Generator[tuple[str | int | float, dict], None, None]: See example
            above.
    """
    target_parent_label_names = target_parent_label_names or set()

    if isinstance(doc_section, dict):
        for key, value in doc_section.items():
            current_target_category_parents = set(target_parent_label_names)
            for doc_label in target_doc_labels:
                if doc_label.match_label(key):
                    current_target_category_parents.add(doc_label.name)

            yield from get_content_under_doc_labels(
                value,
                target_doc_labels,
                target_parent_label_names=current_target_category_parents,
            )
    elif isinstance(doc_section, list):
        for item in doc_section:
            yield from get_content_under_doc_labels(
                item,
                target_doc_labels,
                target_parent_label_names=target_parent_label_names,
            )
    else:
        if target_parent_label_names:
            yield {
                "text": doc_section,
                "target_parent_label_names": target_parent_label_names,
            }


def sent_tokenize_label_text(
    doc_label_text_iterator: Generator[dict[str, str | set[str]], None, None],
    sent_tokenizer: SpacyModel,
) -> list[dict[str, str | int | set[str]]]:
    """
    Iterates over output of get_content_under_doc_labels and returns a list of
    dictionaries containing the tokenized sentences, ancestor DocLabel names
    and the number of the group (the larger text content) each sentence came
    from.

    Args:
        doc_label_tex_iterator (
            Generator[dict[str, Any | set[str]], None, None]):
            Output of get_content_under_doc_labels
        sent_tokenizer (SentTokenizer): Spacy sent tokenizer

    Returns:
        list[dict[str, str | int | set[str]]]: See above.
    """
    sents_with_refs = []

    for i, (d) in enumerate(doc_label_text_iterator):
        text = d["text"]
        target_parent_label_names = d["target_parent_label_names"]

        if type(text) is list:
            text_list = flatten_lists(text)
        else:
            text_list = [text]

        for text in text_list:
            if text is None:
                continue
            if not isinstance(text, (str, int, float)):
                error_str = f"Incompatible type {type(text)} for text label found in "
                raise ValueError(error_str)
            for sent in sent_tokenizer.sent_tokenize(str(text)):
                sents_with_refs.append(
                    {
                        "sentence": sent,
                        "group_id": i,
                        "text_categories": target_parent_label_names,
                    }
                )
    return sents_with_refs


def get_sents_from_doc(
    doc: dict | list, target_doc_labels: list[DocLabel], sent_tokenizer: SpacyModel
) -> list[dict[str, str | int | set[str]]]:
    """"""
    iterator = get_content_under_doc_labels(doc, target_doc_labels=target_doc_labels)
    sents_with_refs = sent_tokenize_label_text(iterator, sent_tokenizer)
    return sents_with_refs


def get_keys_or_values_for_doc_labels_inner(
    doc: Any,
    target_doc_labels: list[DocLabel],
    values_and_doc_labels: list[tuple[Any, DocLabel]] | None = None,
) -> list[tuple[Any, DocLabel]]:
    values_and_doc_labels = values_and_doc_labels or []

    if isinstance(doc, dict):
        for key, value in doc.items():
            for doc_label in target_doc_labels:
                if doc_label.match_label(key):
                    if not doc_label.value_in_attrs and doc_label in [
                        doc_label for value, doc_label in values_and_doc_labels
                    ]:
                        error_str = f'Multiple instances of document-level label "{doc_label.name}" found in '
                        raise ValueError(error_str)
                    if doc_label.value_in_attrs:
                        values_and_doc_labels.append((key, doc_label))
                    else:
                        if not isinstance(value, (str, int, float, bool, NoneType)):
                            error_str = f'Incompatible value "{value}" found for document-level label "{doc_label.name}" in '
                            raise ValueError(error_str)
                        values_and_doc_labels.append((value, doc_label))

            values_and_doc_labels = get_keys_or_values_for_doc_labels_inner(
                value, target_doc_labels, values_and_doc_labels
            )

        return values_and_doc_labels
    elif isinstance(doc, list):
        for item in doc:
            values_and_doc_labels = get_keys_or_values_for_doc_labels_inner(
                item, target_doc_labels, values_and_doc_labels
            )

        return values_and_doc_labels
    return values_and_doc_labels


def get_keys_or_values_for_doc_labels(
    doc: Any,
    target_doc_labels: list[DocLabel],
) -> list[tuple[Any, DocLabel]]:
    values_and_doc_labels = []
    return get_keys_or_values_for_doc_labels_inner(
        doc, target_doc_labels, values_and_doc_labels
    )


def get_doc_level_meta_props(
    doc: dict | list, target_doc_labels: list[DocLabel]
) -> list[dict[str, Any]]:
    """
    Gets values for document-level meta properties from DocLabels. Throws an
    error if more than one key matching DocLabel is found.

    For DocLabels where value_in_attrs is True, the value(s) are the non-"_tag"
    attributes of the corresponding key. Where value_in_attrs is False, the
    value(s) are the value of the correponding key.
    """

    raw_values_and_doc_labels = get_keys_or_values_for_doc_labels(
        doc, target_doc_labels
    )

    meta_props = []

    # Keep track of added values from attribute-type meta values.
    # (They can occur in multiple nodes, so you need to make sure
    # no atrributes are repeated)
    added_label_name_attr_name_pairs = set()

    for value, doc_label in raw_values_and_doc_labels:
        if doc_label.value_in_attrs:
            attrs = dict(value)  # type: ignore
            attrs.pop("_tag")  # type: ignore
            for value_name, value in attrs.items():
                pair = (doc_label.name, value_name)
                if pair in added_label_name_attr_name_pairs:
                    error_str = f'Multiple values for attribute "{value_name}" found for document-level meta label "{doc_label.name}" in '
                    raise ValueError(error_str)
                added_label_name_attr_name_pairs.add(pair)
                meta_value_d = {
                    "label_name": doc_label.name,
                    "name": value_name,
                    "value": value,
                }
                meta_props.append(meta_value_d)

        else:
            meta_value_d = {
                "label_name": doc_label.name,
                "name": doc_label.name,
                "value": value,
            }
            meta_props.append(meta_value_d)

    return meta_props
