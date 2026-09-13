# A basic introduction to Grover's algorithm

### Introduction
After encountering Grover's algorithm through the 3Blue1Brown channel, I found myself struggling to grasp exactly how it worked under the hood. For me, the best path to understanding is building and explaining it myself. My goal here is to deliver a basic but thorough explanation for developers who don't have a background in quantum physics, but are comfortable with basic linear algebra.

### Theory
It is best to release the urge to think about a qubit as a physical particle with mysterious properties. Instead, treat it simply as a state vector. When inspected (measured), this vector collapses into one of the basis vectors.

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle \xrightarrow{\text{Measurement}} \begin{cases} |0\rangle \text{ with probability } |\alpha|^2 \\ |1\rangle \text{ with probability } |\beta|^2 \end{cases}
$$

Like classical bits, an $n$-qubit system has $2^n$ possible states. Each possible state occupies its own row in the state vector in a predetermined order. 

The number assigned to each state is its **probability amplitude**. According to Born’s rule, if you take the absolute square of an amplitude, you get the actual probability of the system collapsing into that state. Because probabilities must add up to 100%, the sum of all absolute squared amplitudes is strictly $1$.

For a single qubit, $|0\rangle$ represents the state $\begin{pmatrix} 1 \\ 0 \end{pmatrix}$ and $|1\rangle$ represents the state $\begin{pmatrix} 0 \\ 1 \end{pmatrix}$. A 2D quantum state is just a linear combination of these basis vectors, with the amplitudes serving as coefficients. A qubit with a state vector containing more than one non-zero amplitude is in **superposition**.

$$
|\psi\rangle = \begin{pmatrix} \alpha \\ \beta \end{pmatrix} = \alpha \begin{pmatrix} 1 \\ 0 \end{pmatrix} + \beta \begin{pmatrix} 0 \\ 1 \end{pmatrix}
$$

Because of quantum mechanics, you can never interact directly with the state vector to read its raw values. Measuring it forces a collapse. Therefore, to compute anything, you must manipulate the state vector blindly using **quantum gates**.

Do not think of a quantum gate as a physical object made from silicon transistors. Think of it as a mathematical matrix that multiplies and transforms your vector. For example, a quantum NOT gate (the Pauli-X gate) flips the amplitudes of $|0\rangle$ and $|1\rangle$.

*Classical NOT Gate:* `NOT(0) = 1`  
*Quantum NOT Gate (Pauli-X):*
$$
X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} \quad \implies \quad \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} \begin{pmatrix} \alpha \\ \beta \end{pmatrix} = \begin{pmatrix} \beta \\ \alpha \end{pmatrix}
$$

It’s important to note that you cannot just invent any matrix and call it a gate. Quantum gates are physically constrained (they must be unitary and reversible). Quantum engineers must figure out how to utilize this highly limited toolkit to build useful algorithms. Quantum computers aren't universally faster than classical ones; they only excel in highly specific areas where clever algorithms exploit these limited matrix operations.

In this project, using the Qiskit library, I replicated a search algorithm that is exponentially more efficient than its classical counterparts. I will break down the general idea behind the steps, and then dive into the matrix math of how each step is actually performed.

### Grover’s Algorithm
For simplicity, I will explain the core concepts using a small number of qubits, but this expands directly to larger systems. In reality, large matrices (like a NOT gate applied to 2 qubits simultaneously) are simply the Kronecker product of the basic $2 \times 2$ matrices that assemble them.

$$
X \otimes X = \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} \otimes \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} = \begin{pmatrix} 0 & 0 & 0 & 1 \\ 0 & 0 & 1 & 0 \\ 0 & 1 & 0 & 0 \\ 1 & 0 & 0 & 0 \end{pmatrix}
$$

To start a quantum algorithm, we initialize the system in a "pure" state of all zeros, and immediately put it into a uniform superposition so every possible answer has an equal amplitude. For a system with $N$ states, every amplitude becomes $\frac{1}{\sqrt{N}}$. The gate that performs this is the **Hadamard (H) gate**:

$$
H = \frac{1}{\sqrt{2}} \begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix} \quad \implies \quad H|0\rangle = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix}
$$

Grover’s algorithm relies on manipulating these amplitudes in two repeating steps:
1. **The Oracle:** We single out the answer we seek (the target) and flip its sign from positive to negative. Because all other states remain positive, this drops the target's amplitude far below the overall average.
2. **The Diffusion:** We reflect every state's amplitude around that new average. Since the target was artificially pushed far below the mean, bouncing it across the average causes it to shoot up, drastically increasing its size while shrinking everything else.

By repeating this Oracle-Diffusion cycle a calculated number of times ($\approx \frac{\pi}{4}\sqrt{N}$), we continuously amplify the target's probability until measuring the circuit is guaranteed to give us the right answer.

![Diffusion Graph](assets/diffusion_graph.png)

### The Oracle
In principle, every problem has its own specific Oracle. The goal is to create a quantum operation that "spits out" a minus sign if the answer is correct, and does nothing otherwise. Because quantum operations are strictly linear, if you pass a vector in superposition, the Oracle will only flip the specific component that aligns with the target.

In my implementation, I want my target to be the state of all ones, $|11\dots1\rangle$. Therefore, I need to flip only the amplitude of that specific state. If we look at the simplest setup of just one qubit (a 2D vector), it's like wanting to flip only the y-axis component.

$$
\begin{pmatrix} \alpha \\ \beta \end{pmatrix} \xrightarrow{\text{Oracle}} \begin{pmatrix} \alpha \\ -\beta \end{pmatrix}
$$

Those who remember their linear algebra well can already guess what that matrix looks like:

$$
Z = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}
$$

For a single qubit, this operation is called the **Pauli-Z gate**. For multiple qubits, we need an **MCZ (Multi-Controlled Z)** gate, which phase-flips only the $|11\dots1\rangle$ state in the state vector (the very last amplitude).

The catch is that while Qiskit has a basic Z gate, there is no native MCZ gate in the basic physical hardware set. We have to build a workaround using the **MCX (Multi-Controlled X) gate**. The MCX takes a group of "control" qubits and one "target" qubit. If the control group is all ones, it flips the target. (For a single qubit setup, the MCX is just a standard NOT gate).

This is the foundation we’ll build upon. We want to manipulate a vector using a matrix such that if the vector is on the span of $\vec{v}$, the output is $-\vec{v}$. But if it’s orthogonal to $\vec{v}$, it remains unchanged. In matrix notation:

$$
Z \begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} x \\ -y \end{pmatrix}
$$

To achieve this using the X gate, I’ll introduce two common basis vectors used in quantum algorithms: $|+\rangle$ and $|-\rangle$.

$$
|+\rangle = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ 1 \end{pmatrix}, \quad |-\rangle = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 \\ -1 \end{pmatrix}
$$

Notice what happens if we pass them through a NOT (X) gate:

$$
X|+\rangle = |+\rangle
$$
$$
X|-\rangle = -|-\rangle
$$

These two vectors are orthonormal to each other, meaning they form a valid basis. If we want an operation that phase-flips only $|1\rangle$ and leaves $|0\rangle$ alone, we need to temporarily change our basis so that $|1\rangle$ lands on $|-\rangle$ and $|0\rangle$ lands on $|+\rangle$. We do exactly that with the Hadamard gate.

$$
H|0\rangle = |+\rangle
$$
$$
H|1\rangle = |-\rangle
$$

Because the Hadamard matrix is its own inverse, we can switch the basis back to the original simply by applying another Hadamard. In summary: $H \to X \to H = Z$.

One way to prove this is through straightforward matrix multiplication:

$$
\frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix} \begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix} \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix} = \begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix} = Z
$$

A much more interesting approach is to acknowledge that the two eigenvectors of the NOT matrix are $|+\rangle$ and $|-\rangle$, with eigenvalues of $1$ and $-1$ respectively. The NOT matrix essentially flips the space around $|+\rangle$. If we rotate the space beforehand so that the unwanted answers land on $|+\rangle$, and then rotate it back afterwards, the entire operation leaves the unwanted answers completely unaffected while perfectly flipping the sign of our target.

To bridge this into scenarios with more than 1 qubit, let's look at an $n$-qubit system. We’ll choose one qubit to be our target, and all the rest will be controls. The process is:
1. Apply Hadamard only on the target.
2. Apply MCX across all qubits (using the chosen target).
3. Apply Hadamard again only on the target.

Let's walk through what happens in each possible scenario:

* **A) Some controls are 0:** The first H puts the target in a superposition. Because not all controls are 1, the MCX does absolutely nothing. The second H just cancels out the first H. Net effect: zero change.
* **B) Controls are 1, but target is 0:** The first H transforms the target $|0\rangle$ into $|+\rangle$. The MCX activates, but since $|+\rangle$ is an eigenvector with an eigenvalue of 1, the MCX doesn't change it. The second H transforms it right back to $|0\rangle$.
* **C) Controls are 1, and target is 1:** The first H transforms the target $|1\rangle$ into $|-\rangle$. The MCX activates. Since $|-\rangle$ is the eigenvector with an eigenvalue of -1, it flips the sign. The second H returns the target to $|1\rangle$, but that negative sign remains factored out in front of the entire state. The output becomes:

$$
|1\rangle \otimes |1\rangle \dots \otimes |1\rangle \otimes (-|1\rangle) = (-1) \left( |1\rangle \otimes |1\rangle \dots \otimes |1\rangle \right)
$$

* **D) The entire system is in superposition:** A superposition is just a linear combination of all possible outcomes. Because every quantum matrix operation ($U$) is strictly linear, our H-MCX-H block will act on each component exactly as described above, and then sum them back together. 

$$
U(\alpha|x\rangle + \beta|y\rangle) = \alpha U|x\rangle + \beta U|y\rangle
$$
