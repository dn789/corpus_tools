from pathlib import Path
from typing import Any

import pylangacq
from pylangacq.chat import Utterance

from backend.utils.functions import detect_and_convert_childes_age


def process_cha_file(file_path: Path) -> dict[str, Any]:
    try:
        reader = pylangacq.read_chat(file_path.__str__())
    except UnicodeDecodeError as e:
        return {"error": str(e), "file_path": file_path}

    file_d = {"file_path": file_path}
    sent_dicts = []

    for utt in reader.utterances():
        sent_dict = {}
        sent_dict = process_utterance(utt)  # type: ignore
        sent_dicts.append(sent_dict)

    file_d["sent_dicts"] = sent_dicts  # type: ignore

    meta_properties = []
    headers = reader.headers()[0]
    for h_name, h_d in headers.items():
        if h_name == "Participants":
            meta_properties.extend(flatten_participants(h_d))
        else:
            # Temporary fix
            if isinstance(h_d, (list, set)):
                h_d = str(h_d)

            meta_properties.append({"label_name": h_name, "name": h_name, "value": h_d})
    file_d["meta_properties"] = meta_properties  # type: ignore
    return file_d


def flatten_participants(
    participants: dict[str, dict[str, dict[str, str]]],
) -> list[dict[str, str]]:
    flattened = []
    for p_name, p_d in participants.items():
        for p_k, p_v in p_d.items():
            if p_v:
                if isinstance(p_v, (list, set)):
                    p_v = str(p_v)
                name = f"{p_name}-{p_k}"
                if type(p_v) is str and (age := detect_and_convert_childes_age(p_v)):
                    value = age
                else:
                    value = p_v
                flattened.append(
                    {"label_name": "Participants", "name": name, "value": value}
                )
    return flattened


def process_utterance(utt: Utterance) -> dict[str, Any]:
    sent_dict = {}
    sent_dict["text_categories"] = [utt.participant]  # type: ignore
    sent_dict["sent_tiers"] = {}
    for i, (label, tier) in enumerate(utt.tiers.items()):
        if not i:
            sent_dict["sentence"] = tier
        else:
            sent_dict["sent_tiers"][label] = tier
    return sent_dict
