#ifndef INCOMPLETE_QR_H
#define INCOMPLETE_QR_H

// input: sparse matrix A (m by n, in CSC format),
//        drop tolerance for keeping intermediate Q sparse,
//        and sparsity structure of n by n upper triangular factor R
// output: values in R so that R is roughly the R in the QR decomposition of A (i.e. Cholesky factor of A^T*A)
//
// Note that Rvalue should already be allocated when calling this function

void incomplete_qr(int m, int n, const int *Acolstart, const int *Arowindex, const double *Avalue,
                   double Qdroptol,
                   const int *Rcolstart, const int *Rrowindex, double *Rvalue, double *Rdiag);

#endif
