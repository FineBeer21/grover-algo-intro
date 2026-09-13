import math
import time
import csv
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def initialHadamard (qc, n):
    qbits = list(range(n))
    qc.h(qbits)

def mcz (qc, target, n):
    # Because there's no real MCZ for flipping the target you need a workaround with MCX
    # An easy way to look at it as matrix multipication. H * X * H = Z
    # But you can also think about that the 2 eigenvectors of X matrix are |+> and |-> with eigenvalue of 1 and -1 respectively.
    # So by using MCX on a target qbit, it will throw -1 (and not change the target) only if the target is |->. Meaning only if the target before the hadamard was |1>!

    control = [i for i in range(n) if i != target]
    qc.h(target)
    qc.mcx(control, target)
    qc.h(target)

def oracle (qc, target, n):
    mcz(qc, target, n)

def diffusion(qc, n):
    # Switch base to put the "pure Hadamardy" vector on the |000...000> vector. Then X the entire vector in order to use MCZ (like in the oracle)
    # it doesnt matter if we flip all but one, or just the one. The latter is easier so MCZ only the |000...00> vector, then bringing everything back.
    # In summery: H > X > MCZ > X > H. MCZ being H > MCX > H

    qbits = list(range(n))

    qc.h(qbits)
    qc.x(qbits)
    mcz(qc, 0 , n)
    qc.x(qbits)
    qc.h(qbits)


def run(max_n):
    simulator = AerSimulator()
    print("Starting...")
    csv_data = [["n_qubits", "N_states", "calculation", "time_ms", "success_rate"]]

    for n in range(2, max_n + 1):
        N = 1 << n
        target = n - 1
        optimal_iterations = max(1, int((math.pi / 4) * math.sqrt(N)))
        calculation = 0 # Monitoring how many gate calculation I'm using, the spesific amount is chosen quite arbitrarly but should make a difference

        start_time = time.perf_counter()

        qc = QuantumCircuit(n)
        initialHadamard(qc, n)
        calculation += n
            
        for _ in range(optimal_iterations):
            oracle(qc, target, n)
            calculation += 3 
            diffusion(qc, n)
            calculation += 7
                
        qc.measure_all()
            
        # Compiling
        compiled_circuit = transpile(qc, simulator)
        job = simulator.run(compiled_circuit, shots=1000)
        counts = job.result().get_counts()

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000

        # Checking success rate
        target_state = '1' * n  # We're looking in for the state with only ones.
        success_rate = counts.get(target_state, 0) / 1000.0

        csv_data.append([n, N, calculation, elapsed_ms, success_rate])
        print(f"n={n} | States: {N} | Calculation: {calculation} | Time: {elapsed_ms:.2f}ms | Success: {success_rate*100:.1f}%\n")
    
    with open("grover_benchmark.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(csv_data)
    print("results saved")


run(16)