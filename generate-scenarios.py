import csv
import re
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


def output_latex(
    tables: tuple[list[list[str]], list[list[str]]],
    actors: list,
    filename: str,
    regex: str,
) -> None:
    # Open the LaTeX file
    with Path(filename).open("r", encoding="UTF-8") as file:
        lines = file.readlines()

    # Find the line number to insert tables
    line_number = -1
    for i, line in enumerate(lines):
        if re.search(re.escape(regex), line):
            line_number = i + 1
            break

    # If regex is not matched in any line
    if line_number == -1:
        print(f"No line in {filename} matches the provided regular expression.")
        return

    def generate_latex_table(
        table: list[list[str]], description: str | None = None
    ) -> list[str]:
        begin = "\n\\begin{xltabular}{\\textwidth}{|" + "X|" * len(actors) + "}\n"
        latex_table = [begin]
        if description:
            latex_table.append("\\hline\n")
            latex_table.append(
                "\\multicolumn{"
                + str(len(actors))
                + "}{|p{\\dimexpr\\linewidth-2\\tabcolsep\\relax}|}{"
                + description
                + "} \\\\\n"
            )
        latex_table.append("\\hline\n")
        latex_table.append(" & ".join(actors) + " \\\\\n")
        latex_table.append("\\hline\n")
        for row in table:
            latex_table.append(" & ".join(row) + " \\\\\n")
        latex_table.append("\\hline\n")
        latex_table.append("\\end{xltabular}\n")
        return latex_table

    # Convert tables to LaTeX format
    latex_tables = [f"% START {regex[1:5]} TABLES\n"]
    latex_tables.extend(generate_latex_table(tables[0]))
    for description, table in tables[1]:
        latex_tables.extend(generate_latex_table(table, description))
    latex_tables.append(f"% END {regex[1:5]} TABLES\n")

    # Remove previous tables if they exist
    start_table_line = -1
    end_table_line = -1
    for i, line in enumerate(lines):
        if line.strip() == f"% START {regex[1:5]} TABLES":
            start_table_line = i
        elif line.strip() == f"% END {regex[1:5]} TABLES":
            end_table_line = i
            break
    if start_table_line != -1 and end_table_line != -1:
        lines = lines[:start_table_line] + lines[end_table_line + 1 :]

    # Insert tables into LaTeX file
    lines = lines[:line_number] + latex_tables + lines[line_number:]

    # Write back to the LaTeX file
    with Path(filename).open("w", encoding="UTF-8") as file:
        file.writelines(lines)


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
            # output_csv(tables, data["Actors"], f"{use_case}.csv")
            output_latex(tables, data["Actors"], "report.tex", data["Regex"])


if __name__ == "__main__":
    main()
