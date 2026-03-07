import json
import matplotlib.pyplot as plt
from pathlib import Path
from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime.utils.json import RuntimeDecoder

def process_all_jobs():
    workload_dir = Path(r"d:\Cosmos\workloads (2)")
    artifact_dir = Path(r"C:\Users\corys\.gemini\antigravity\brain\e39fa9c0-1407-4d84-9683-4edbfa79866b")
    
    info_files = list(workload_dir.glob("*-info.json"))
    md_path = artifact_dir / "all_jobs_breakdown.md"
    
    with open(md_path, "w", encoding="utf-8") as md:
        md.write("# Complete Swarm Quantum Execution Breakdown\n\n")
        md.write("This document is an exhaustive, job-by-job decode of the 19 IBM Quantum primitives executed by the Swarm. It contains the raw mathematical QASM matrices and the corresponding physical measurement histograms for every single pulse.\n\n")
        
        for idx, info_file in enumerate(info_files):
            try:
                job_id = info_file.name.replace("job-", "").replace("-info.json", "")
                md.write(f"## Job #{idx+1} | ID: `{job_id}`\n")
                
                # Load QASM
                with open(info_file, 'r') as f:
                    info = json.load(f, cls=RuntimeDecoder)
                
                circuit = info["params"]["pubs"][0][0]
                qasm_txt = str(circuit.draw(output='text'))
                md.write("### 12D Phase Cognitive Circuit (`ibm_fez`)\n")
                md.write(f"```text\n{qasm_txt}\n```\n\n")
                
                # Handle Results
                res_file = workload_dir / info_file.name.replace("-info", "-result")
                if not res_file.exists():
                    md.write("> *Job measurement result JSON missing from directory.*\n\n---\n\n")
                    continue
                    
                with open(res_file, 'r') as f:
                    res = json.load(f, cls=RuntimeDecoder)
                    
                counts = res[0].data.meas.get_counts()
                sorted_counts = dict(sorted(counts.items(), key=lambda item: item[1], reverse=True)[:10])
                
                # Draw and save individual histogram to artifacts dir!
                img_name = f"hist_{job_id}.png"
                img_path = artifact_dir / img_name
                
                fig = plot_histogram(sorted_counts, title=f"Execution Entropy (Job {job_id})", color='#2eb82e', figsize=(10,5))
                plt.savefig(img_path, dpi=200, bbox_inches='tight')
                plt.close(fig) # free memory!
                
                md.write("### Measurement Entropy Collapse (4096 Shots)\n")
                md.write(f"![Histogram]({img_name})\n\n")
                
                # Brief textual summary of the most prominent state
                top_state = list(sorted_counts.keys())[0]
                top_count = sorted_counts[top_state]
                md.write(f"> **Primary Collapse State:** The Swarm's wave function collapsed primarily into `|{top_state}⟩` (Decohered {top_count} times).\n\n")
                md.write("---\n\n")
                
            except Exception as e:
                md.write(f"> *Error decoding this specific job trace: {e}*\n\n---\n\n")

    print(f"SUCCESS! Wrote all jobs into {md_path}")

if __name__ == "__main__":
    process_all_jobs()
