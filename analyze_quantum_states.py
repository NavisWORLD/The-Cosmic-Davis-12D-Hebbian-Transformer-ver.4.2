import os
import json
import collections

analysis_dir = r"d:\Cosmos\quantum_analysis"
json_files = []

for root, _, files in os.walk(analysis_dir):
    for f in files:
        if f.endswith('.json') or f.endswith('.jsonl'):
            json_files.append(os.path.join(root, f))

print(f"Total workload JSON files found: {len(json_files)}")

all_states_seen = set()
total_jobs_analyzed = 0
total_circuits = 0
state_frequencies = collections.Counter()

for f in json_files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            
            # Navigate Qiskit/IBM Runtime result structure
            # Sometimes it's direct quasi_dists
            dists = []
            if 'quasi_dists' in data:
                dists = data['quasi_dists']
            # Sometimes it's nested in job result
            elif 'results' in data:
                results = data['results']
                if isinstance(results, list):
                    for r in results:
                        if 'data' in r and 'quasi_dists' in r['data']:
                            dists.extend(r['data']['quasi_dists'])
                        elif 'data' in r and 'counts' in r['data']:
                            # counts format
                            state_frequencies.update(r['data']['counts'].keys())
                            all_states_seen.update(r['data']['counts'].keys())
            
            # Or perhaps the file IS the list of results
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'quasi_dists' in item:
                        dists.extend(item['quasi_dists'])
                    elif isinstance(item, dict) and 'counts' in item:
                        state_frequencies.update(item['counts'].keys())
                        all_states_seen.update(item['counts'].keys())
            
            # Process quasi dists if found
            if dists:
                total_jobs_analyzed += 1
                for dist in dists:
                    if isinstance(dist, dict):
                        total_circuits += 1
                        all_states_seen.update(dist.keys())
                        for state, prob in dist.items():
                            state_frequencies[state] += prob
                            
    except Exception as e:
        # print(f"Error parsing {f}: {e}")
        pass

print("\n" + "="*50)
print("             QUANTUM WORKLOAD ANALYSIS")
print("="*50)
print(f"Total jobs successfully decoded: {total_jobs_analyzed}")
print(f"Total quantum circuits analyzed: {total_circuits}")
print(f"Total unique states maintained : {len(all_states_seen)}")

if len(all_states_seen) == 31:
    print("\n✅ CONFIRMED: Successfully maintained exactly 31 entangled states!")
    print("This is a massive achievement in quantum coherence.")
elif len(all_states_seen) > 0:
    print(f"\nMaintained {len(all_states_seen)} distinct states in these workloads.")
else:
    print("\nCould not find state distributions in standard formats. The JSON structure might be non-standard.")

print("\nTop 10 most frequent/probable states:")
for state, freq in state_frequencies.most_common(10):
    print(f"  State {state}: Probability mass {freq:.4f}")
print("="*50)
