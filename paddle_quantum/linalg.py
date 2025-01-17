# !/usr/bin/env python3
# Copyright (c) 2022 Institute for Quantum Computing, Baidu Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
The common linear algorithm in paddle quantum.
"""

from typing import Optional
import paddle
import math
import numpy as np
import scipy
from functools import reduce

import paddle_quantum


def abs_norm(mat: paddle.Tensor) -> float:
    r""" tool for calculation of matrix norm

    Args:
        mat: matrix

    Returns:
        norm of mat

    """
    mat = mat.cast('complex64')
    return paddle.norm(paddle.abs(mat)).item()


def dagger(mat: paddle.Tensor) -> paddle.Tensor:
    r""" tool for calculation of matrix dagger

    Args:
        mat: matrix

    Returns:
        The dagger of matrix

    """
    return paddle.conj(mat.T)


def is_hermitian(mat: paddle.Tensor, eps: Optional[float] = 1e-6) -> bool:
    r""" verify whether mat ``P`` is Hermitian

    Args:
        mat: matrix
        eps: tolerance of error

    Returns:
        determine whether :math:`mat - mat^\dagger = 0`

    """
    shape = mat.shape
    if len(shape) != 2 or shape[0] != shape[1] or math.log2(shape[0]) != math.ceil(math.log2(shape[0])):
        # not a mat / not a square mat / shape is not in form 2^n x 2^n
        return False
    return abs_norm(mat - dagger(mat)) < eps


def is_projector(mat: paddle.Tensor, eps: Optional[float] = 1e-6) -> bool:
    r""" verify whether mat ``P`` is a projector

    Args:
        mat: matrix
        eps: tolerance of error

    Returns:
        determine whether :math:`PP - P = 0`

    """
    shape = mat.shape
    if len(shape) != 2 or shape[0] != shape[1] or math.log2(shape[0]) != math.ceil(math.log2(shape[0])):
        # not a mat / not a square mat / shape is not in form 2^n x 2^n
        return False
    return abs_norm(mat @ mat - mat) < eps


def is_unitary(mat: paddle.Tensor, eps: Optional[float] = 1e-5) -> bool:
    r""" verify whether mat ``P`` is a unitary

    Args:
        mat: matrix
        eps: tolerance of error

    Returns:
        determine whether :math:`PP^\dagger - I = 0`

    """
    shape = mat.shape
    if len(shape) != 2 or shape[0] != shape[1] or math.log2(shape[0]) != math.ceil(math.log2(shape[0])):
        # not a mat / not a square mat / shape is not in form 2^n x 2^n
        return False
    return abs_norm(mat @ dagger(mat) - paddle.cast(paddle.eye(shape[0]), mat.dtype)) < eps


def hermitian_random(num_qubits: int) -> paddle.Tensor:
    r"""randomly generate a :math:`2^n \times 2^n` hermitian matrix

    Args:
        num_qubits: log2(dimension)

    Returns:
         a :math:`2^n \times 2^n` hermitian matrix

    """
    assert num_qubits > 0
    n = 2 ** num_qubits
    vec = paddle.randn([n, n]) + 1j * paddle.randn([n, n])
    mat = vec @ dagger(vec)
    return mat / paddle.trace(mat)


def orthogonal_projection_random(num_qubits: int) -> paddle.Tensor:
    r"""randomly generate a :math:`2^n \times 2^n` rank-1 orthogonal projector

    Args:
        num_qubits: log2(dimension)

    Returns:
         a :math:`2^n \times 2^n` orthogonal projector and its eigenstate
    """
    assert num_qubits > 0
    n = 2 ** num_qubits
    vec = paddle.randn([n, 1]) + 1j * paddle.randn([n, 1])
    mat = vec @ dagger(vec)
    return mat / paddle.trace(mat)


def unitary_hermitian_random(num_qubits: int) -> paddle.Tensor:
    r"""randomly generate a :math:`2^n \times 2^n` hermitian unitary

    Args:
        num_qubits: :math:`\log_{2}(dimension)`

    Returns:
         a :math:`2^n \times 2^n` hermitian unitary matrix
         
    """
    proj_mat = orthogonal_projection_random(num_qubits)
    id_mat = paddle.eye(2 ** num_qubits)
    return (2 + 0j) * proj_mat - id_mat


def unitary_random_with_hermitian_block(num_qubits: int) -> paddle.Tensor:
    r"""randomly generate a unitary :math:`2^n \times 2^n` matrix that is a block encoding of a :math:`2^{n/2} \times 2^{n/2}` Hermitian matrix

    Args:
        num_qubits: :math:`\log_{2}(dimension)`

    Returns:
         a :math:`2^n \times 2^n` unitary matrix that its upper-left block is a Hermitian matrix

    """
    assert num_qubits > 0
    dtype = paddle_quantum.get_dtype()
    mat0 = hermitian_random(num_qubits - 1).numpy()
    id_mat = np.eye(2 ** (num_qubits - 1))
    mat1 = 1j * scipy.linalg.sqrtm(id_mat - np.matmul(mat0, mat0))

    mat = np.block([[mat0, mat1], [mat1, mat0]])

    return paddle.to_tensor(mat, dtype=dtype)


def unitary_random(num_qubits: int) -> paddle.Tensor:
    r"""randomly generate a :math:`2^n \times 2^n` unitary

    Args:
        num_qubits: :math:`\log_{2}(dimension)`

    Returns:
         a :math:`2^n \times 2^n` unitary matrix

    """
    unitary = scipy.stats.unitary_group(2 ** num_qubits)
    return paddle.to_tensor(unitary)


def haar_orthogonal(num_qubits: int) -> paddle.Tensor:
    r""" randomly generate an orthogonal matrix following Haar random, referenced by arXiv:math-ph/0609050v2

    Args:
        num_qubits: number of qubits

    Returns:
        a :math:`2^n \times 2^n` orthogonal matrix
        
    """
    # Matrix dimension
    dim = 2 ** num_qubits
    # Step 1: sample from Ginibre ensemble
    ginibre = (np.random.randn(dim, dim))
    # Step 2: perform QR decomposition of G
    mat_q, mat_r = np.linalg.qr(ginibre)
    # Step 3: make the decomposition unique
    mat_lambda = np.diag(mat_r) / abs(np.diag(mat_r))
    mat_u = mat_q @ np.diag(mat_lambda)
    return paddle.to_tensor(mat_u)


def haar_unitary(num_qubits: int) -> paddle.Tensor:
    r""" randomly generate a unitary following Haar random, referenced by arXiv:math-ph/0609050v2

    Args:
        num_qubits: number of qubits

    Returns:
        a :math:`2^n \times 2^n` unitary
        
    """
    # Matrix dimension
    dim = 2 ** num_qubits
    # Step 1: sample from Ginibre ensemble
    ginibre = (np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)) / np.sqrt(2)
    # Step 2: perform QR decomposition of G
    mat_q, mat_r = np.linalg.qr(ginibre)
    # Step 3: make the decomposition unique
    mat_lambda = np.diag(mat_r) / np.abs(np.diag(mat_r))
    mat_u = mat_q @ np.diag(mat_lambda)
    return paddle.to_tensor(mat_u)


def haar_state_vector(num_qubits: int, is_real: Optional[bool] = False) -> paddle.Tensor:
    r""" randomly generate a state vector following Haar random

        Args:
            num_qubits: number of qubits
            is_real: whether the vector is real, default to be False

        Returns:
            a :math:`2^n \times 1` state vector
            
    """
    # Vector dimension
    dim = 2 ** num_qubits
    if is_real:
        # Generate a Haar random orthogonal matrix
        mat_orthog = haar_orthogonal(num_qubits)
        # Perform u onto |0>, i.e., the first column of o
        phi = mat_orthog[:, 0]
    else:
        # Generate a Haar random unitary
        unitary = haar_unitary(num_qubits)
        # Perform u onto |0>, i.e., the first column of u
        phi = unitary[:, 0]

    return paddle.to_tensor(phi)


def haar_density_operator(num_qubits: int, rank: Optional[int] = None, is_real: Optional[bool] = False) -> paddle.Tensor:
    r""" randomly generate a density matrix following Haar random

        Args:
            num_qubits: number of qubits
            rank: rank of density matrix, default to be False refering to full ranks
            is_real: whether the density matrix is real, default to be False

        Returns:
            a :math:`2^n \times 2^n` density matrix
    """
    dim = 2 ** num_qubits
    rank = rank if rank is not None else dim
    assert 0 < rank <= dim, 'rank is an invalid number'
    if is_real:
        ginibre_matrix = np.random.randn(dim, rank)
        rho = ginibre_matrix @ ginibre_matrix.T
    else:
        ginibre_matrix = np.random.randn(dim, rank) + 1j * np.random.randn(dim, rank)
        rho = ginibre_matrix @ ginibre_matrix.conj().T
    rho = rho / np.trace(rho)
    return paddle.to_tensor(rho / np.trace(rho))


def NKron(matrix_A: np.ndarray, matrix_B: np.ndarray, *args: np.ndarray) -> np.ndarray:
    r""" calculate Kronecker product of at least two matrices

    Args:
        matrix_A: matrix
        matrix_B: matrix
        *args: other matrices

    Returns:
        Kronecker product of matrices
    """
    return reduce(lambda result, index: np.kron(result, index), args, np.kron(matrix_A, matrix_B), )