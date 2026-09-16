from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import csv

def initialHadamard(qc, n):
    qbits = list(range(n))
    qc.h(qbits)

def mcz(qc, target, n):
    control = [i for i in range(n) if i != target]
    qc.h(target)
    qc.mcx(control, target)
    qc.h(target)

def oracle(qc, target, n):
    mcz(qc, target, n)

def diffusion(qc, n):
    qbits = list(range(n))
    qc.h(qbits)
    qc.x(qbits)
    mcz(qc, 0 , n)
    qc.x(qbits)
    qc.h(qbits)

service = QiskitRuntimeService(channel="ibm_quantum_platform", token="token") 

backend = service.least_busy(operational=True, simulator=False, min_num_qubits=5)
print(f"sending to backend: {backend.name}")

ns = [3, 4, 5]
iterations_map = {3: 2, 4: 3, 5: 4} # Optimal iterations for each n
compiled_circuits = []

for n in ns:
    target = n - 1
    qc = QuantumCircuit(n)
    
    initialHadamard(qc, n)
    
    for _ in range(iterations_map[n]):
        oracle(qc, target, n)
        diffusion(qc, n)
        
    qc.measure_all()
    
    print(f"transpiling for n={n}...")
    compiled_circuit = transpile(qc, backend)
    compiled_circuits.append(compiled_circuit)

print("submitting all circuits via SamplerV2 (Batch)")
sampler = Sampler(mode=backend)
sampler.options.default_shots = 1000

job = sampler.run(compiled_circuits)
print(f"submitted. job ID: {job.job_id()}")

print("waiting for results...")
result = job.result()

filename = f"ibm_results_batch_{job.job_id()}.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    
    for idx, n in enumerate(ns):
        compiled_circuit = compiled_circuits[idx]
        counts = result[idx].data.meas.get_counts()
        
        ops = dict(compiled_circuit.count_ops())
        depth = compiled_circuit.depth()
        total_shots = sum(counts.values())
        
        writer.writerow([f"--- Results for n={n} Qubits ---", "", ""])
        writer.writerow(["Circuit Depth", depth, ""])
        writer.writerow(["Physical Gates", str(ops), ""])
        writer.writerow(["State", "Counts", "Probability"])
        
        for state, count in sorted(counts.items(), key=lambda item: item[1], reverse=True):
            probability = count / total_shots
            writer.writerow([state, count, f"{probability*100:.1f}%"])
            
        writer.writerow([]) 

print(f"\nAll results cleanly saved to {filename}")
