import os
import subprocess

import yaml

git_result = subprocess.run(
    ["git", "diff", "--name-status", "development...HEAD"],
    capture_output=True,
    text=True,
)
changed_files = git_result.stdout.strip().split("\n")
deleted_files = [file.split("\t")[1] for file in changed_files if file.startswith("D")]


def get_guid_or_none(file):
    if file.endswith(".meta"):
        # read content of deleted file
        git_result = subprocess.run(
            ["git", "show", f"HEAD^:{file}"],
            capture_output=True,
            text=True,
        )
        content = git_result.stdout.strip()
        parsed_content = yaml.safe_load(content)
        if "guid" in parsed_content:
            return parsed_content["guid"]
    return None


def find_references(guid, referenced_file):
    # search for guid in all .prefab and .unity files in Assets folder
    for root, dirs, files in os.walk("Assets"):
        for file in files:
            if file.endswith(".prefab") or file.endswith(".unity"):
                with open(os.path.join(root, file), "r") as f:
                    content = f.read()
                    if guid in content:
                        print(
                            f"{guid} referenced in {os.path.join(root, file)}\n        deleted file: {referenced_file}"
                        )


for file in deleted_files:
    if file.endswith(".meta"):
        guid = get_guid_or_none(file)
        if guid:
            find_references(guid, file)
