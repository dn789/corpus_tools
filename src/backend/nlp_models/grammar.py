import re
from typing import Any

from gramformer import Gramformer

from tqdm import tqdm
from transformers import pipeline


def filter_sent(sent: str) -> bool:
    sent = sent.strip()
    if sent and len(sent.split()) > 1:
        return True
    return False


class GramformerModel:
    def __init__(self) -> None:
        self.model = Gramformer(models=1, use_gpu=True)

    def correct(self, sentence: str) -> str:  # type: ignore
        for sent in self.model.correct(sentence, max_candidates=1):  # type: ignore
            return sent

    def highlight(self, input_sentence: str, corrected_sentence: str) -> str:
        return self.model.highlight(input_sentence, corrected_sentence)

    def highlight_and_parse_errors(
        self, input_sentence: str, corrected_sentence: str
    ) -> list[dict[str, str]]:
        try:
            highlighted = self.model.highlight(input_sentence, corrected_sentence)
        except IndexError:
            return []
        errors = self.parse_errors(highlighted)
        return errors

    def parse_errors(self, highlighted_sentence: str) -> list[dict[str, str]]:
        errors = []
        for error in re.findall(
            r"<c type='(.+?)' edit='(.+?)'>(.+?)</c>", highlighted_sentence
        ):
            if len(error) != 3:
                errors.append({"parse_error": error})
                continue
            error_d = {"type": error[0], "edit": error[1], "original": error[2]}
            errors.append(error_d)
        return errors

    def get_errors(self, sentence: str) -> list[dict[str, str]]:
        corrected = self.correct(sentence)
        highlighted = self.highlight(sentence, corrected)
        errors = self.parse_errors(highlighted)
        return errors


class GrammarlyModel:
    def __init__(self) -> None:
        self.pipeline = pipeline(
            "text2text-generation",
            model="grammarly/coedit-large",
            device="cuda:0",
            truncation=True,
            max_length=256,
        )
        assert self.pipeline.device.__str__() == "cuda:0"

    def __call__(self, text: str) -> str:
        prompt = f"Fix grammatical errors in this sentence: {text}"
        results = self.pipeline(prompt)[0]  # type: ignore
        return results["generated_text"]  # type: ignore

    def pipe(self, samples: list[str], batch_size=1) -> list[str]:
        output = []
        with tqdm(samples) as prog_bar:
            for result in self.pipeline(
                self._generator(samples), batch_size=batch_size
            ):  # nopep8 # type: ignore
                output.append(result[0]["generated_text"])  # type: ignore
                prog_bar.update(1)
                prog_bar.refresh()
        return output

    def _generator(self, samples: list[str]):
        for sent in samples:
            prompt = f"Fix grammatical errors in this sentence: {sent}"
            yield prompt


class GrammarTask:
    def __init__(self):
        self.gramformer = GramformerModel()
        self.grammarly = GrammarlyModel()

    def get_errors(
        self,
        sent_dicts: list[dict[str, Any]],
        batch_size: int = 8,
        frontend_connect: Any = None,
    ) -> list[tuple[str]]:
        results = []
        sent_dicts = list(sent_dicts)[:25]
        original_sents = []
        for sent_d in sent_dicts:
            original_sents.append(sent_d["sentence"])
        if frontend_connect:
            frontend_connect.taskInfo.emit(
                "Finding grammatical errors. This might take a while...", None
            )
        corrected_sents = self.grammarly.pipe(original_sents, batch_size=batch_size)
        for original_sent, corrected_sent in zip(original_sents, corrected_sents):
            error_ds = self.gramformer.highlight_and_parse_errors(
                original_sent, corrected_sent
            )
            for i, error_d in enumerate(error_ds):
                results.append(
                    (
                        error_d["type"],
                        error_d["original"],
                        error_d["edit"],
                        original_sent,
                        sent_dicts[i]["file_path"],
                    )
                )
        return results
