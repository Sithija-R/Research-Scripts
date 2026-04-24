import os
import csv
import json
from pydriller import Repository

# Paths
WORKDIR = "/home/sithija/research_pipeline/defects4j_workdir"
PROJECT = "Time"
CSV_PATH = f"/home/sithija/research_pipeline/defects4j/framework/projects/{PROJECT}/active-bugs.csv"
OUTPUT_JSON = "/home/sithija/research_pipeline/output/final/time_methods_commit_hash_dataset.json"

all_bugs = {}

# Read CSV
with open(CSV_PATH, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        bug_id = row['bug.id']
        buggy_commit = row['revision.id.buggy']   # ✅ NEW
        fixed_commit = row['revision.id.fixed']

        buggy_dir = os.path.join(WORKDIR, f"{PROJECT}-{bug_id}-b")
        fixed_dir = os.path.join(WORKDIR, f"{PROJECT}-{bug_id}-f")

        if not os.path.exists(buggy_dir) or not os.path.exists(fixed_dir):
            print(f"⚠️ Bug directories not found for {PROJECT}-{bug_id}. Skipping.")
            continue

        print(f"🔹 Processing {PROJECT}-{bug_id}")
        print(f"   🐞 Buggy commit: {buggy_commit}")
        print(f"   ✅ Fixed commit: {fixed_commit}")

        bug_methods = {}
        try:
            # Traverse only the fixed commit
            for commit in Repository(fixed_dir, single=fixed_commit).traverse_commits():
                for mf in commit.modified_files:
                    if mf.new_path and mf.changed_methods:
                        bug_methods[mf.new_path] = [m.name for m in mf.changed_methods]

        except Exception as e:
            print(f"⚠️ Error processing {PROJECT}-{bug_id}: {e}")
            continue

        if bug_methods:
            all_bugs[f"{PROJECT}-{bug_id}"] = {
                "buggy_commit": buggy_commit,   # ✅ NEW
                "fixed_commit": fixed_commit,
                "methods": bug_methods
            }

# Save dataset to JSON
with open(OUTPUT_JSON, "w") as f:
    json.dump(all_bugs, f, indent=4)

print(f"✅ Extraction complete! Dataset saved to {OUTPUT_JSON}")
