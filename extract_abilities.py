import collections
import csv
import dataclasses
import json
from typing import Dict

from System import System
from utils.format import bullet

@dataclasses.dataclass
class Ability:
    class_calling: str
    name: str
    description: str
    source: str
    tier: str

    def json(self) -> Dict[str, str]:
        return self.__dict__

    @staticmethod
    def from_json(json_data: Dict[str, str]) -> 'Ability':
        return Ability(** json_data)

def main():
    # TODO These files need manual updating at apt times
    with open('Spire_ Character Tracker - Rules Engine.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        spire_lines = list(reader)

    abilities = collections.defaultdict(dict)

    for line in spire_lines:
        name = line['Ability'].title().replace("'S", "'s")

        description = line['Description']

        description = description.replace('• ', bullet(''))

        ability = Ability(
            class_calling=line['Class'],
            name=name,
            description=description,
            tier=line['Tier'],
            source=line['Source']
        )

        abilities[System.SPIRE.value][ability.name.lower()] = ability

    with open('Heart_ Character Tracker - Rules Engine w_ Expanded Abilities.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        heart_lines = list(reader)

    for line in heart_lines:
        name: str = line['Ability'].title().replace("'S", "'s")

        if ' - ' in name:
            continue
        elif '(base)' in name:
            continue

        description = line['Ability Description']

        description = description.replace('• ', bullet(''))

        ability = Ability(
            class_calling=line['Class / Calling'],
            name=name,
            description=description,
            tier=line['Tier'],
            source=line['Source']
        )

        abilities[System.HEART.value][ability.name.lower()] = ability

    with open('all_abilities.json', 'w', encoding='utf-8') as f:
        json.dump(abilities, f, indent=4, default=lambda j: j.json())

if __name__ == '__main__':
    main()