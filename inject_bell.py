import sys

file_path = r'd:\Cosmos\Cosmos\web\server.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

target = 'class QuantumConfig(BaseModel):'

insert_code = '''
@app.post("/api/quantum/bell")
async def quantum_run_bell(shots: int = 20):
    """Run Bell state on REAL IBM Quantum hardware."""
    try:
        from Cosmos.integration.hackathon.quantum_proof import get_quantum_proof
        qp = get_quantum_proof()
        job = await qp.run_bell_state(shots=min(shots, 100))
        return JSONResponse({
            "success": True,
            "job_id": job.job_id,
            "backend": job.backend,
            "circuit": "bell_state",
            "qubits": 2,
            "shots": job.shots,
            "status": job.status,
            "portal_url": f"https://quantum.ibm.com/jobs/{job.job_id}",
            "message": "Job submitted to REAL quantum hardware! Check IBM portal.",
            "warning": "Jobs can take minutes to hours in the queue."
        })
    except Exception as e:
        import traceback
        import logging
        logging.error(f"Quantum Bell Error: {e}", exc_info=True)
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)

'''

if target in content and "/api/quantum/bell" not in content:
    content = content.replace(target, insert_code + target)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected successfully!")
else:
    print("Target not found or already injected.")
