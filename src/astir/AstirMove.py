from dataclasses import dataclass
import string
import re
from typing import Dict, Optional, Union, Set

from src.utils.format import bold, bullet

@dataclass
class AstirMove:
    name: str
    description_template: string.Template
    playbook: str = 'Basic'
    traits: Optional[Dict[str, str]] = None
    results: Optional[Dict[str, str]] = None
    outcome_template: Optional[string.Template] = None

    DEFAULT_FAILURE_OUTCOME = 'You fail.'

    def __post_init__(self):
        if self.results is not None:
            if '0-6' not in self.results:
                self.results['0-6'] = 'You fail.'

            if self.outcome_template is None:
                self.outcome_template = string.Template("${outcome}")

    def _substitute_traits(self) -> str:
        if any(desc == "" for desc in self.traits.values()):
            listed = list(self.traits.keys())
            if len(self.traits) > 1:
                traits_text = ', '.join("+" + trait.upper() for trait in listed[:-1]) + f", or +{listed[-1].upper()}"
            else:
                traits_text = listed[0].upper()
        else:
            traits_text_components = []

            for trait, desc in self.traits.items():
                traits_text_components.append(bullet(bold("+" + trait) + f": {desc}"))

            traits_text = "\n" + '\n'.join(traits_text_components)

        return traits_text

    def _substitute_results(self):
        results_text_components = []

        seen: Set[str] = set()

        for result, desc in self.results.items():
            clean_desc = desc.lower().strip(string.whitespace + string.punctuation)
            new_desc = desc
            for seen_text in seen:
                if seen_text in clean_desc:
                    replacement = 'As above' if clean_desc.find(seen_text) == 0 else 'as above'

                    new_desc = re.sub(
                        pattern=re.escape(seen_text),
                        repl=replacement,
                        string=desc,
                        count=1,
                        flags=re.IGNORECASE
                    )

            seen.add(clean_desc)

            results_text_components.append(bullet(bold(result) + f": {new_desc}"))

        results_text = '\n'.join(results_text_components)

        return results_text

    @property
    def description(self):
        substitutions = {}

        if "${traits}" in self.description_template.template:
            substitutions['traits'] = self._substitute_traits()

        if "${results}" in self.description_template.template:
            substitutions['results'] = self._substitute_results()

        description = self.description_template.substitute(substitutions)

        if self.outcome_template is not None:
            description += self.outcome_template.substitute({
                'outcome': ''
            }).strip()

        return description

    def get_outcome(self, total: int):
        if self.results is None:
            raise ValueError(f'No results for move "{self.name}".')

        if total >= 10:
            outcome = self.results['10+']
        elif total >= 7:
            outcome = self.results['7-9']
        else:
            outcome = self.results['0-6']

        if total < 7 and self.results['0-6'] == self.DEFAULT_FAILURE_OUTCOME:
            response = outcome
        else:
            response = self.outcome_template.substitute({
                'outcome': outcome,
            })

        return response

    @classmethod
    def from_json(cls, name: str, move_data: Dict[str, Union[str, Dict[str, str]]]) -> 'AstirMove':
        description_template = string.Template(move_data.pop('description'))

        if 'outcome' in move_data:
            outcome_template = string.Template(move_data.pop('outcome'))
        else:
            outcome_template = None

        return AstirMove(name=name, description_template=description_template, outcome_template=outcome_template, ** move_data)

