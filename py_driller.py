from pydriller import Repository
import json
import os

# ================= CONFIG =================
REPO_PATH = "/home/sithija/research_pipeline/commons-time"
FIXED_METHODS_JSON = "/home/sithija/research_pipeline/output/final/time_methods_commit_hash_dataset.json"
OUTPUT_JSON = "/home/sithija/research_pipeline/output/final/time_method_evolution_dataset.json"

VERSION_LIMIT = 3   # Number of historical versions (excluding buggy/fixed)
BUG_LIMIT = 170      # Number of bug IDs to process from the JSON

# >>> ADDED (ONLY THIS) <<<
BIG_CHANGE_THRESHOLD = 20  # filter for big commits only

# ================= HELPER: ROBUST EXTRACTION =================
def extract_method_source(mf, method_name):
    """Robustly extracts method source code and metadata."""
    for m in mf.methods:
        if m.name == method_name:
            if mf.source_code and m.start_line and m.end_line:
                lines = mf.source_code.splitlines()
                code = "\n".join(lines[m.start_line-1 : m.end_line])
                return code, getattr(m, "nloc", None), getattr(m, "complexity", None)

            if hasattr(m, 'source_code') and m.source_code:
                return m.source_code, getattr(m, "nloc", None), getattr(m, "complexity", None)
    return None, None, None

# ================= LOAD DATA =================
with open(FIXED_METHODS_JSON) as f:
    fixed_methods = json.load(f)

method_histories = {}
bug_counter = 0

# ================= PROCESS EACH BUG =================
for bug_id, bug_data in fixed_methods.items():
    if BUG_LIMIT is not None and bug_counter >= BUG_LIMIT:
        break

    bug_counter += 1
    fixed_h = bug_data["fixed_commit"]
    buggy_h = bug_data["buggy_commit"]
    method_histories[bug_id] = {}

    print(f"\n🔹 Processing {bug_id} | Buggy Hash: {buggy_h[:8]}")

    for file_path, methods in bug_data["methods"].items():
        if "test" in file_path.lower(): 
            continue

        method_histories[bug_id][file_path] = {}

        for method_name in methods:
            versions = []

            # --- STEP 1: BUGGY VERSION ---
            for commit in Repository(REPO_PATH, single=buggy_h).traverse_commits():
                for mf in commit.modified_files:
                    if (mf.new_path or mf.old_path) == file_path:
                        code, nloc, comp = extract_method_source(mf, method_name)
                        if code:
                            versions.append({
                                "commit": commit.hash,
                                "label": "history",
                                "type": "BUGGY_STATE",
                                "date": str(commit.committer_date),
                                "nloc": nloc,
                                "complexity": comp,
                                "source_code": code
                            })

            # --- STEP 2: HISTORY (FILTERED FOR BIG CHANGES ONLY) ---
            try:
                repo = Repository(REPO_PATH, to_commit=f"{buggy_h}^", order='reverse').traverse_commits()
                history_found = 0

                for commit in repo:

                    # >>> ADDED FILTER 1: BIG CHANGE FILTER <<<
                    total_changes = commit.insertions + commit.deletions
                    if total_changes < BIG_CHANGE_THRESHOLD:
                        continue

                    method_changed = any(
                        m.name == method_name
                        for mf in commit.modified_files
                        if (mf.new_path or mf.old_path) == file_path
                        for m in mf.changed_methods
                    )

                    if not method_changed:
                        continue

                    for mf in commit.modified_files:
                        if (mf.new_path or mf.old_path) == file_path:
                            code, nloc, comp = extract_method_source(mf, method_name)
                            if code:
                                versions.append({
                                    "commit": commit.hash,
                                    "label": "history",
                                    "date": str(commit.committer_date),
                                    "nloc": nloc,
                                    "complexity": comp,
                                    "source_code": code
                                })
                                history_found += 1

                    if history_found >= VERSION_LIMIT:
                        break

            except Exception as e:
                print(f"      ⚠️ History Walk Error: {e}")

            # --- STEP 3: FIXED VERSION ---
            for commit in Repository(REPO_PATH, single=fixed_h).traverse_commits():
                for mf in commit.modified_files:
                    if (mf.new_path or mf.old_path) == file_path:
                        code, nloc, comp = extract_method_source(mf, method_name)
                        if code:
                            versions.append({
                                "commit": commit.hash,
                                "label": "fixed",
                                "date": str(commit.committer_date),
                                "nloc": nloc,
                                "complexity": comp,
                                "source_code": code
                            })

            method_histories[bug_id][file_path][method_name] = versions
            print(f"      ✅ Method '{method_name}' captured with {len(versions)} versions.")

# ================= SAVE =================
with open(OUTPUT_JSON, "w") as f:
    json.dump(method_histories, f, indent=4)

print(f"\n🚀 Success! Dataset saved to {OUTPUT_JSON}")
