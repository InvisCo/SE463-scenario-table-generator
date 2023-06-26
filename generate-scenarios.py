import csv
from io import TextIOWrapper
from pathlib import Path

import yaml
from tabulate import tabulate

DATA_PATH = Path("data/")


def load_yaml(yaml_path: Path) -> dict:
    with yaml_path.open("r") as file:
        return yaml.safe_load(file)


def process_scenario(
    scenario: list,
    actors: list,
) -> tuple[list[list[str]], list[list[str]]]:
    main_table: list[list[str]] = []
    special_tables: list[list[str]] = []
    main_counter = 0
    alternative_counter = 0
    error_counter = 0

    for step in scenario:
        for actor, action in step.items():
            if actor in actors:
                main_counter += 1
                row = [""] * len(actors)
                row[actors.index(actor)] = f"{main_counter}. {action}"
                main_table.append(row)
            elif actor in ["Alternatives", "Exceptions"]:
                for special in action:
                    if actor == "Alternatives":
                        alternative_counter += 1
                        special_counter = alternative_counter
                    if actor == "Exceptions":
                        error_counter += 1
                        special_counter = error_counter

                    special_table = []
                    special_counter_sub = main_counter
                    for special_action in special["Actions"]:
                        for special_actor, special_act in special_action.items():
                            row = [""] * len(actors)
                            row[
                                actors.index(special_actor)
                            ] = f"{actor[0]}{special_counter}.{special_counter_sub}. {special_act}"
                            special_table.append(row)
                            special_counter_sub += 1

                    row = [""] * len(actors)
                    row[0] = f'Go To: {special["Goto"]}'
                    special_table.append(row)

                    special_tables.append(
                        (
                            f'{actor} {special_counter}: {special["Description"]}',
                            special_table,
                        )
                    )

    return main_table, special_tables


def output_csv(
    tables: tuple[list[list[str]], list[list[str]]],
    actors: list,
    filename: str = "tables.csv",
) -> None:
    with Path(DATA_PATH, filename).open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(actors)
        writer.writerows(tables[0])
        writer.writerow([])  # add empty row
        writer.writerow([])  # add empty row
        for description, table in tables[1]:
            writer.writerow([description])
            writer.writerow(actors)
            writer.writerows(table)
            writer.writerow([])  # add empty row
            writer.writerow([])  # add empty row


def output_tabulated(
    use_case: str,
    tables: tuple[list[list[str]], list[list[str]]],
    actors: list,
    file: TextIOWrapper,
) -> None:
    table_format = "simple_outline"

    file.write(f"{use_case}\n\n")
    # Write main table
    file.write(tabulate(tables[0], headers=actors, tablefmt=table_format))

    # Write special tables
    for description, table in tables[1]:
        file.write(f"\n\n{description}\n")
        file.write(tabulate(table, headers=actors, tablefmt=table_format))

    file.write(
        "\n\n\n==============================================================================\n\n\n"
    )


def main() -> None:
    with Path(DATA_PATH, "tables.txt").open("w", encoding="utf-8") as file:
        for use_case_file in DATA_PATH.glob("*.yaml"):
            # Load YAML data
            data = load_yaml(use_case_file)

            # Process the scenario
            tables = process_scenario(data["Scenario"], data["Actors"])

            # Output
            use_case = use_case_file.name.split(".")[0]
            output_tabulated(use_case, tables, data["Actors"], file)
            output_csv(tables, data["Actors"], f"{use_case}.csv")


if __name__ == "__main__":
    main()
