#include <iostream>
#include <cmath>
#include <ostream>
#include <fstream>
#include <chrono>
#include <ratio>

void initial_hadamard(double* state, int N){

    double amplitude = 1.0 / std::sqrt(N);

    for (int i = 0; i < N; i++){
        state[i] = amplitude;
    }
}

void oracle(double* state, int targetIndex, long& iterations){
    // with an example as simple as this is, it's not too difficult of a step to grasp
    state[targetIndex] *= -1.0;
    iterations++;
}

void diffusion(double* state, int N, long& iterations){
    //therefore a running time of o(N), and because it will be called around pi/4 * sqrt(N) the the entire run time is o(N*sqrt(N))
    double sum = 0.0;
    for(int i = 0; i < N; i++){
        sum += state[i];
        iterations++;
    }

    double mean = sum / N;

    for(int i = 0; i < N; i++){
        state[i] = 2.0 * mean - state[i];
        iterations++;
    }
}

int main () {
    // for analyzing runtime
    std::ofstream file("results_cpp.csv");

    file << "n,N,iterations,time_ms,target_probability\n";

    std::cout << "starting..." << std::endl;

    for (int i = 3; i < 17; i++){

        long iterations = 0;
        int n = i;
        int N = 1 << n; 
        int targetIndex = N - 1;

        double* state_vector = new double [N];

        // optimal iteration number is PI/4 * sqrt(N)
        int optimal_iter = std::round((M_PI / 4) * sqrt(N));

        auto startTime = std::chrono::high_resolution_clock::now();

        initial_hadamard(state_vector, N);

        for (int i = 0; i < optimal_iter; i++){
            oracle(state_vector, targetIndex, iterations);
            diffusion(state_vector, N, iterations);
        }

        auto endTime = std::chrono::high_resolution_clock::now();

        std::chrono::duration<double, std::milli> duration = endTime - startTime;
        double time_ms = duration.count();

        double target_prob = state_vector[targetIndex] * state_vector[targetIndex];

        file << n << "," 
             << N << "," 
             << iterations << "," 
             << time_ms << "," 
             << target_prob * 100.0 << "\n";

        std::cout << "Done n=" << n 
                  << " (N=" << N << ") | " 
                  << "Iter: " << iterations << " | "
                  << "Time: " << time_ms << " ms | "
                  << "Prob: " << target_prob * 100.0 << "%" << std::endl;

        delete[] state_vector;
    }

    file.close();
    std::cout << "finished" << std::endl;
    return 0;
}