#include <iostream>
#include <string.h>
#include <stdlib.h>
#include <omp.h>
#include <vector>
#include <cstring>

#include "likwid-stuff.h"

const char* dgemm_desc = "Blocked dgemm, OpenMP-enabled";

void square_dgemm_basic(int n, double* A, double* B, double* C) {
    for (int i = 0; i < n; i++) { // rows
        for (int j = 0; j < n; j++) { // columns
            double square_sum = C[i*n + j];
            for (int k = 0; k < n; k++) {
                // C[i, j] = C[i, j] + A[i, n] * B[n, j];
                square_sum += A[i*n + k] * B[k*n + j];
            }
            C[i*n + j] = square_sum;
        }
    }
}

void copy_block(double *dest, double *src, int n, int block_size) {
    for (int y = 0; y < block_size; y++) {
        std::memcpy(&dest[y * block_size],
            &src[y * n],
            block_size * sizeof(double));
    }
}

void write_block(double *dest, double *src, int n, int block_size) {
    for (int y = 0; y < block_size; y++) {
        std::memcpy(&dest[y * n],
            &src[y * block_size],
            block_size * sizeof(double));
    }
}

/* This routine performs a dgemm operation
 *  C := C + A * B
 * where A, B, and C are n-by-n matrices stored in row-major format.
 * On exit, A and B maintain their input values. */
void square_dgemm_blocked(int n, int block_size, double* A, double* B, double* C) 
{
    const int Nb = n / block_size;
    const int block_arr_size = block_size * block_size;

#pragma omp parallel
    {
        LIKWID_MARKER_START(MY_MARKER_REGION_NAME);

        double* buf_mem = new double[block_arr_size * 3];
        double* An = &buf_mem[0];
        double* Bn = &buf_mem[block_arr_size];
        double* Cn = &buf_mem[block_arr_size * 2];

#pragma omp for collapse(2)
        for (int i = 0; i < Nb; i++) {   // row
            for (int j = 0; j < Nb; j++) {   // col
                // calculate this so we store it in register
                double* Cpos = &C[i * n * block_size + j * block_size];
                copy_block(Cn, Cpos, n, block_size);

                for (int k = 0; k < Nb; k++) {
                    copy_block(An, &A[i * n * block_size + k * block_size], n, block_size);
                    copy_block(Bn, &B[k * n * block_size + j * block_size], n, block_size);

                    square_dgemm_basic(block_size, An, Bn, Cn);
                }

                write_block(Cpos, Cn, n, block_size);
            }
        }

        delete[] buf_mem;

        LIKWID_MARKER_STOP(MY_MARKER_REGION_NAME);
    }
}
