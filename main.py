# This is an AI-generated CLI version of my past code (o3-mini, accessed through Zed's assistant panel, paid for by GitHub Copilot). A copy of the old code is attached at the end of the file.
"""
Chinese Vocabulary Utility CLI

This script provides various commands to handle Chinese vocabulary,
including adding vocabulary from Integrated Chinese data, merging with
a ground truth file, reviewing vocabulary definitions, importing custom
vocabulary, exporting to a Fresh Cards/Anki-compatible format, and loading
vocabulary from an HTML table.

Functions:
  add(lessons, file): Adds vocabulary from the given lessons of Integrated
                      Chinese Level 1 Part 1 to the given vocabulary file.
  merge(file): Merges the given vocabulary file into the ground truth file.
  review(file): Allows review and modification of the vocabulary definitions.
  custom(file, lesson=None): Allows the user to add custom vocabulary entries.
  truth_to_card(file, accept=lambda card: True): Exports the ground truth file to
                      a text file for use with Anki/other apps.
  load_xml(filein, fileout, level): Loads vocabulary from an HTML table in a
                      specific format into the given vocabulary file.

To get help on how to use a command:
    python dev/main.py -h
    python dev/main.py add -h
    python dev/main.py merge -h
    ...etc.
"""

import argparse
import json
import os
import re
import subprocess

###############################################
# TODO:                                       #
#   [X] Implement review function, which will #
#     take in a card json file and check all  #
#     English to improve efficiency           #
#   [X] Implement cards function, which will  #
#     export the ground truth json to a       #
#     Fresh Cards-compatible format           #
#   [X] Implement custom function, which will #
#     allow the user to import custom cards   #
#   [X] Implement supplemental function,      #
#     which will scan Canvas tables to get    #
#     supplemental cards                      #
#   [X] Add "change Chinese" option for       #
#     conflict resolution                     #
###############################################

matches = {
    "adj": "adjective",
    "adv": "adverb",
    "conj": "conjunction",
    "interj": "interjection",
    "m": "measure word",
    "mv": "modal verb",
    "n": "noun",
    "nu": "numeral",
    "p": "particle",
    "pn": "proper noun",
    "pr": "pronoun",
    "prefix": "prefix",
    "prep": "preposition",
    "qp": "question particle",
    "qpr": "question pronoun",
    "t": "time",
    "v": "verb",
    "vc": "verb + component",
    "vo": "verb + object",
}


def add(lessons, file):
    """
    Add vocabulary from Integrated Chinese Level 1 Part 1 associated with the
    provided lessons to the card JSON file.

    Args:
      lessons: List of lesson numbers (ints) to include.
      file: Output JSON file to save the vocabulary.
    """
    ic = json.load(open("ic_truth.json"))
    cards = []
    for card in ic["plecoflash"]["cards"]["card"]:
        phrase = card["entry"]["headword"]
        if len(phrase[0]) != 1:
            phrase = list(filter(lambda a: a["+@charset"] == "sc", phrase))[0][
                "+content"
            ]
        pinyin = card["entry"]["pron"]["+content"]
        english = card["entry"]["defn"]
        level = card["catassign"]["+@category"].split()[-1]
        if int(level) not in lessons:
            continue
        cards.append(
            {
                "english": english,
                "pinyin": pinyin,
                "chinese": phrase,
                "level": int(level),
            }
        )
    json.dump(cards, open(file, "w"), ensure_ascii=False)
    os.system("npx prettier --write " + file)
    rev = input("Review definitions? (y/Y for yes, any other key for no): ")
    if rev.lower() == "y":
        review(file)


def merge(file):
    """
    Merge a given vocabulary JSON file into the ground truth file (truth.json)
    and invoke an interactive conflict resolution if multiple entries are
    found for the same Chinese string.
    """
    ground = json.load(open("truth.json"))
    for key in ground.keys():
        ground[key] = [ground[key]]
    cards = json.load(open(file))
    for card in cards:
        key = card["chinese"]
        if key not in ground.keys():
            ground[key] = [card]
        else:
            ground[key] = [*ground[key], card]

    def resolve_conflict(key):
        print("============= CONFLICT =============")
        for i in range(len(ground[key])):
            print(f"**** V{i + 1}: ****")
            print(f"\teng: {ground[key][i]['english']}")
            print(f"\tpin: {ground[key][i]['pinyin']}")
            print(f"\tchi: {ground[key][i]['chinese']}")
            print(f"\tlev: {ground[key][i]['level']}")
            print("\n")
        print("Resolve conflict:")
        print(" * type V1, V2, ... to substitute that version's value")
        print(" * empty fields are substituted with the first version's value")
        print(
            " * type MULTIPLE_MODE in the english field to enter multiple card mode. In this mode, instead of combining conflicting cards, you assign them distinct Chinese characters."
        )

        def getv(v):
            value = str(input(f"{v}: ").strip())
            if not value:
                print("\tUsing version 1")
                return str(ground[key][0][v])
            if (
                len(value) == 2
                and value[0] == "V"
                and int(value[1]) <= len(ground[key])
            ):
                print(f"\tUsing version {value}")
                return str(ground[key][int(value[1:]) - 1][v])
            return value

        card = {}
        en = getv("english")
        if en == "MULTIPLE_MODE":
            print("###### MULTIPLE MODE ######")
            print("Choose a new set of characters for each conflicting card.")
            keep = input(
                "Which version card would you like to preserve the characters of (1, 2, ...)? "
            )
            while not keep.isdigit():
                print("Invalid input. Please enter a number.")
                keep = input(
                    "Which version card would you like to preserve the characters of (1, 2, ...)? "
                )
            print(f"Got it. Card V{keep} will not be changed.")
            keep = int(keep)
            for i in range(1, len(ground[key]) + 1):
                if i == keep:
                    continue
                while True:
                    newchars = input(f"New characters for version {i}: ")
                    while newchars in ground:
                        print(f"Character '{newchars}' already in use.")
                        newchars = input(f"New characters for version {i}: ")
                    newcard = ground[key][i - 1]
                    newcard["chinese"] = newchars
                    print("Final card:")
                    print(f"\teng: {newcard['english']}")
                    print(f"\tpin: {newcard['pinyin']}")
                    print(f"\tchi: {newcard['chinese']}")
                    print(f"\tlvl: {newcard['level']}")
                    redo = input(
                        "Good? Type any key to continue or N/n to restart changing the characters of this card: "
                    )
                    if redo.lower() == "n":
                        continue
                    else:
                        ground[newchars] = [newcard]
                        break
            keep = ground[key][keep - 1]
            return keep
        card["english"] = en
        card["pinyin"] = getv("pinyin")
        card["chinese"] = getv("chinese")
        level = getv("level")
        while not level.isdigit():
            print("Invalid input. Please enter a number.")
            level = getv("level")
        card["level"] = int(level)
        ground[key] = [card]
        print("Final card:")
        print(f"\teng: {card['english']}")
        print(f"\tpin: {card['pinyin']}")
        print(f"\tchi: {card['chinese']}")
        print(f"\tlvl: {card['level']}")
        redo = input(
            "Good? Type any key to continue or N/n to restart the conflict resolution: "
        )
        if redo.lower() == "n":
            return resolve_conflict(key)
        return card

    keys_to_handle = list(filter(lambda a: len(ground[a]) > 1, ground.keys()))
    for key in keys_to_handle:
        if len(ground[key]) > 1:
            ground[key] = [resolve_conflict(key)]
    for key in ground.keys():
        ground[key] = ground[key][0]
    json.dump(ground, open("truth.json", "w"), ensure_ascii=False)
    os.system("npx prettier --write truth.json")


def review(file):
    """
    Review vocabulary in a given JSON file and interactively adjust
    English definitions. Also expands grammatical shorthand if possible.
    """
    cards = json.load(open(file))
    i = 0
    print("Basic rules:")
    print(
        "\tCard details will be shown. You will decide whether to keep the same definition or change the definition."
    )
    print(
        "\tA warning will be shown if the card does not have a known grammar type. The reviewer will generally expand grammar types."
    )
    print(
        "\tEscape codes:\n\t\tenter to keep the same definition. UP followed by a number, e.g., 'UP2' to go back that many cards."
    )
    print("\t")
    while i < len(cards):
        splits = re.split(r"(:|\+)", cards[i]["english"])
        determine = True
        if len(splits) < 2 or not all(
            map(lambda x: x.strip() in matches, splits[0].split(","))
        ):
            determine = False
        else:
            main = list(map(lambda a: matches[a.strip()], splits[0].split(",")))
            cards[i]["english"] = f"{', '.join(main)}:{''.join(splits[2:])}"

        print(
            f"Card (l{cards[i]['level']}):\n\ten: {cards[i]['english']}\n\tpy: {cards[i]['pinyin']}\n\tzh: {cards[i]['chinese']}"
        )

        if not determine:
            print("Unable to determine grammar type.")
        eng = input("\tverdict: ").strip()
        if eng == "":
            cards[i]["english"] = cards[i]["english"]
        elif eng.startswith("UP"):
            i -= int(eng[2:])
            if i < 0:
                i = 0
            continue
        else:
            cards[i]["english"] = eng
        i += 1
    print("All done!")
    json.dump(cards, open(file, "w"), ensure_ascii=False)
    os.system("npx prettier --write cards.json")


def custom(file, lesson=None):
    """
    Import custom vocabulary interactively into a JSON file.
    The user enters vocabulary details. Use numbered pinyin (e.g. ni3hao2);
    type 'EXIT_PROG' in the English field to terminate import,
    and 'DEL{N}' (e.g. DEL2) to delete the last N cards.

    Args:
      file: Output JSON file for the custom vocabulary.
      lesson: (Optional) Default lesson number for all entries.
    """

    def convert_pinyin(
        numbered_pinyin: str,
    ) -> str:  # WARNING: AI-generated code, use with caution
        tone_map = {
            "a": ["a", "ā", "á", "ǎ", "à", "a"],
            "e": ["e", "ē", "é", "ě", "è", "e"],
            "i": ["i", "ī", "í", "ǐ", "ì", "i"],
            "o": ["o", "ō", "ó", "ǒ", "ò", "o"],
            "u": ["u", "ū", "ú", "ǔ", "ù", "u"],
            "ü": ["ü", "ǖ", "ǘ", "ǚ", "ǜ", "ü"],
        }
        """Convert numbered pinyin to pinyin with tone marks."""
        # Replace 'v' with 'ü'
        numbered_pinyin = numbered_pinyin.lower().replace("v", "ü")

        # Split into syllables
        syllables = numbered_pinyin.split()
        result = []

        for syllable in syllables:
            # Extract tone number (default to 0 if no tone number)
            tone = 0
            for i in range(len(syllable)):
                if syllable[i] in "12345":
                    tone = int(syllable[i])
                    syllable = syllable[:i] + syllable[i + 1 :]
                    break

            # Find the vowel to modify based on precedence
            vowels = "aeoiuü"
            vowel_positions = [(c, i) for i, c in enumerate(syllable) if c in vowels]
            if not vowel_positions:
                result.append(syllable)
                continue

            # Apply precedence rules (a > o > e > i > u > ü)
            vowel_to_change = min(vowel_positions, key=lambda x: vowels.index(x[0]))
            vowel, position = vowel_to_change

            # Replace the vowel with its toned version
            new_vowel = tone_map[vowel][tone]
            new_syllable = syllable[:position] + new_vowel + syllable[position + 1 :]
            result.append(new_syllable)

        return " ".join(result)

    print("=============== CUSTOM IMPORTS ===============")
    print("\tUse numbered pinyin, e.g. ni3hao2")
    print("\tTo exit, type 'EXIT_PROG' into the definition field")
    print("\tTo delete the last N cards, type 'DEL{N}' e.g. 'DEL2'")
    if lesson is not None:
        print(f"\tDefault lesson set: {lesson}")
    print("\t")
    cards = []
    while True:
        english = input("\tenglish: ").strip()
        if english.upper() == "EXIT_PROG":
            break
        elif english.startswith("DEL") and english[3:].strip().isdigit():
            n = int(english[3:])
            cards = cards[:-n]
        else:
            pinyin = convert_pinyin(input("\tpinyin: ").strip())
            chinese = input("\tchinese: ").strip()
            thisl = str(lesson)
            if lesson is None:
                while not thisl.isdigit():
                    thisl = input("\tlesson: ")
            thisl = int(thisl)
            card = {
                "english": english,
                "pinyin": pinyin,
                "chinese": chinese,
                "level": thisl,
            }
            print("Final card:")
            print(f"\teng: {card['english']}")
            print(f"\tpin: {card['pinyin']}")
            print(f"\tchi: {card['chinese']}")
            print(f"\tlvl: {card['level']}")
            redo = input("Good? Type any key to continue or N/n to restart")
            if redo.lower() == "n":
                continue
            cards.append(card)
    json.dump(cards, open(file, "w"), indent=4, ensure_ascii=False)


def truth_to_card(file, accept=lambda card: True):
    """
    Export the ground truth JSON (truth.json) to a text file in a format
    compatible with Fresh Cards / Anki.

    Args:
      file: Output text file.
      accept: Optional function for filtering cards (default accepts all cards).
    """
    cards = filter(lambda a: accept(a[1]), json.load(open("truth.json")).items())
    out = ""
    for item in cards:
        card = item[1]
        out += f"front-text: {card['english']}"
        out += f"\nback-text: {card['chinese']} ({card['pinyin']})"
        out += f"\ntags: ic{card['level']}"
        out += "\n\n"
    # dump to file
    with open(file, "w") as f:
        f.write(out)


def load_xml(filein, fileout, level):
    """
    Load vocabulary from an HTML table (assumed to be in a specific format)
    in the given input file and save it as a JSON file with the given level.

    Args:
       filein: Input HTML file.
       fileout: Output JSON file.
       level: Lesson/level number (int) to assign to all imported cards.
    """

    def run_command(command):  # WARNING: AI-generated code, use with caution
        """
        Runs a shell command and returns its output as a string.

        Args:
            command: The command to execute as a string.

        Returns:
            The output of the command as a string, or None if an error occurred.
        """
        try:
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,  # Capture output as text (strings)
                check=True,  # Raise CalledProcessError for non-zero return codes
            )
            return process.stdout.strip()  # remove leading/trailing whitespace
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            print(f"Stderr: {e.stderr}")  # print the error output
            return None
        except FileNotFoundError as e:
            print(f"Command not found: {e}")
            return None
        except Exception as e:  # catch other potential exceptions.
            print(f"An unexpected error occurred: {e}")
            return None

    listed = run_command(f"uv run pip list")
    if "html2text" not in listed:
        print("Installing html2text...")
        run_command(f"uv pip install html2text")
    cards = []
    markdown = run_command(f"uv run html2text {filein}")
    for line in markdown.split("\n"):
        if line.count("|") == 2:
            splits = list(map(lambda a: a.strip(), line.split("|")))
            card = {
                "chinese": splits[0],
                "pinyin": splits[1],
                "english": splits[2],
                "level": level,
            }
            cards.append(card)
    json.dump(cards, open(fileout, "w"), indent=4, ensure_ascii=False)
    # body = json.loads(run_command(f"yq -p=xml -o=json {filein}"))["tbody"]["tr"]

    # def traverse(json):
    #     if isinstance(json, (str, int, float, bool)) or json is None:
    #         return []
    #     elif isinstance(json, dict):
    #         t = []
    #         if "+content" in json.keys():
    #             t = [json["+content"]]
    #         t += [item for sublist in map(traverse, json.values()) for item in sublist]
    #         return t
    #     elif isinstance(json, list):
    #         t = []
    #         for item in json:
    #             t.extend(traverse(item))
    #         return t
    #     else:
    #         raise TypeError(f"Unsupported type: {type(json)}")

    # def getv(v, n):
    #     return "".join(traverse(v["td"][n]["p"]["span"])).replace("&nbsp;", "").strip()

    # cards = []
    # for v in body:
    #     # chinese; pinyin; english
    #     cards.append(
    #         {
    #             "chinese": getv(v, 0),
    #             "pinyin": getv(v, 1),
    #             "english": getv(v, 2),
    #             "level": level,
    #         }
    #     )
    # json.dump(cards, open(fileout, "w"), indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Chinese Vocabulary Utility CLI\n\n"
        "Available subcommands: add, merge, review, custom, truth-to-card, load-xml",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-command help")

    # Subcommand: add
    parser_add = subparsers.add_parser(
        "add",
        help="Add vocabulary from Integrated Chinese (ic_truth.json) to a vocabulary file.",
    )
    parser_add.add_argument(
        "output_file", help="Output JSON file for vocabulary (e.g., cards.json)"
    )
    parser_add.add_argument(
        "-l",
        "--lessons",
        required=True,
        type=str,
        help="Comma-separated list of lesson numbers to include, e.g., '1,2,3'",
    )

    # Subcommand: merge
    parser_merge = subparsers.add_parser(
        "merge", help="Merge a vocabulary file into the ground truth file (truth.json)"
    )
    parser_merge.add_argument(
        "vocab_file", help="Vocabulary JSON file to merge (e.g., cards.json)"
    )

    # Subcommand: review
    parser_review = subparsers.add_parser(
        "review",
        help="Review a vocabulary file and edit English definitions interactively.",
    )
    parser_review.add_argument(
        "file", help="JSON file of vocabulary to review (e.g., cards.json)"
    )

    # Subcommand: custom
    parser_custom = subparsers.add_parser(
        "custom", help="Interactively import custom vocabulary into a JSON file."
    )
    parser_custom.add_argument(
        "output_file",
        help="Output JSON file to save custom vocabulary (e.g., custom.json)",
    )
    parser_custom.add_argument(
        "-l",
        "--lesson",
        type=int,
        default=None,
        help="Default lesson number for all entries (optional)",
    )

    # Subcommand: truth-to-card
    parser_truth = subparsers.add_parser(
        "truth-to-card",
        help="Export the ground truth (truth.json) to a text file for Fresh Cards/Anki.",
    )
    parser_truth.add_argument("output_file", help="Output text file (e.g., export.txt)")

    # Subcommand: load-xml
    parser_xml = subparsers.add_parser(
        "load-xml", help="Load vocabulary from an HTML table file into a JSON file."
    )
    parser_xml.add_argument(
        "input_file", help="Input HTML file containing the vocabulary table"
    )
    parser_xml.add_argument(
        "output_file", help="Output JSON file for vocabulary (e.g., vocabulary.json)"
    )
    parser_xml.add_argument(
        "level",
        type=int,
        help="Level number (int) to assign to all imported vocabulary entries",
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Dispatch to the corresponding function based on command
    if args.command == "add":
        # Parse lessons: comma-separated list of integers
        try:
            lesson_list = [int(x.strip()) for x in args.lessons.split(",")]
        except Exception:
            print(
                "Error parsing lessons. Make sure to provide a comma-separated list of numbers."
            )
            return
        add(lesson_list, args.output_file)
    elif args.command == "merge":
        merge(args.vocab_file)
    elif args.command == "review":
        review(args.file)
    elif args.command == "custom":
        custom(args.output_file, lesson=args.lesson)
    elif args.command == "truth-to-card":
        truth_to_card(args.output_file)
    elif args.command == "load-xml":
        load_xml(args.input_file, args.output_file, args.level)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

"""
Old code is at: https://topaz.github.io/paste/#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
"""
