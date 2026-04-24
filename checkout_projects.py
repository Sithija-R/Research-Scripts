import os
import subprocess

PROJECT = "Time"
WORKDIR = "/home/sithija/research_pipeline/defects4j_workdir"

os.makedirs(WORKDIR, exist_ok=True)

# get bug ids
bug_ids = subprocess.check_output(
    ["defects4j", "bids", "-p", PROJECT]
).decode().split()

for bid in bug_ids:
    buggy_dir = os.path.join(WORKDIR, f"{PROJECT}-{bid}-b")
    fixed_dir = os.path.join(WORKDIR, f"{PROJECT}-{bid}-f")

    print(f"Checking out {PROJECT}-{bid}")

    subprocess.run([
        "defects4j", "checkout",
        "-p", PROJECT,
        "-v", f"{bid}b",
        "-w", buggy_dir
    ])

    subprocess.run([
        "defects4j", "checkout",
        "-p", PROJECT,
        "-v", f"{bid}f",
        "-w", fixed_dir
    ])
