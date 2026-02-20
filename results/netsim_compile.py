import os
import re
import csv

INPUT_DIR = f"C:/Users/hatoa/Aspire/results"
OUTPUT_CSV = "aggregated_results.csv"

# ---------------------------------------
# Helper: parse metrics block
# ---------------------------------------

def parse_metrics(text):
    metrics = {}
    in_block = False

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("=== Simulation Results ==="):
            in_block = True
            continue

        if in_block and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            # Try convert to float if possible
            try:
                value = float(value)
            except ValueError:
                pass

            metrics[key] = value

    return metrics


# ---------------------------------------
# Helper: parse filename metadata
# ---------------------------------------

def parse_filename(filename):
    """
    Example:
    104_leaf_spine_random_workload_ospf_ecmp_configuration_r20.out
    """

    pattern = r"""
        ^\d+_                                  # job index
        (?P<topology>.+?)_                     # topology
        (?P<workload>incast|random_workload|local_group_workload)_  # workload
        (?P<policy>.+?_configuration)_         # policy
        r(?P<rate>\d+)                         # rate
        \.out$
    """

    match = re.match(pattern, filename, re.VERBOSE)

    if not match:
        raise ValueError(f"Filename format not recognized: {filename}")

    return {
        "topology": match.group("topology"),
        "workload": match.group("workload"),
        "policy": match.group("policy"),
        "rate": int(match.group("rate")),
    }
# ---------------------------------------
# Main aggregation
# ---------------------------------------

rows = []

for fname in os.listdir(INPUT_DIR):
    if not fname.endswith(".out"):
        continue

    full_path = os.path.join(INPUT_DIR, fname)

    with open(full_path, "r", errors="ignore") as f:
        content = f.read()

    metrics = parse_metrics(content)

    if not metrics:
        print(f"Skipping (no results block): {fname}")
        continue

    meta = parse_filename(fname)

    row = {**meta, **metrics}
    rows.append(row)

# ---------------------------------------
# Write CSV
# ---------------------------------------

if not rows:
    print("No valid results found.")
    exit()

# Collect all keys dynamically
fieldnames = sorted(set().union(*(row.keys() for row in rows)))

with open(OUTPUT_CSV, "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Saved {len(rows)} rows to {OUTPUT_CSV}")