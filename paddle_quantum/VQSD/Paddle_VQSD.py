# !/usr/bin/env python3
# Copyright (c) 2020 Institute for Quantum Computing, Baidu Inc. All Rights Reserved.
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
Paddle_VQSD: To learn more about the functions and properties of this application,
you could check the corresponding Jupyter notebook under the Tutorial folder.
"""

import numpy
import paddle

import paddle_quantum
from paddle_quantum.ansatz import Circuit
from paddle_quantum.linalg import dagger
from paddle import matmul, trace
from paddle_quantum.VQSD.HGenerator import generate_rho_sigma

SEED = 14

__all__ = [
    "loss_func",
    "Paddle_VQSD",
]


def loss_func(U, rho, sigma):
    # rho_tilda is the quantum state obtained by acting U on rho, which is U*rho*U^dagger
    rho_tilde = matmul(matmul(U, rho), dagger(U))

    # Calculate loss function
    loss = trace(matmul(sigma, rho_tilde))

    return paddle.real(loss), rho_tilde


def Paddle_VQSD(rho, sigma, N=2, ITR=50, LR=0.2):
    r"""
    Paddle_VQSD
    :param rho: Quantum state to be diagonalized
    :param sigma: Quantum state sigma
    :param N: Width of QNN
    :param ITR: Number of iterations
    :param LR: Learning rate
    :return: Diagonalized quantum state after optimization 
    """
    rho = paddle.to_tensor(rho, dtype=paddle_quantum.get_dtype())
    sigma = paddle.to_tensor(sigma, dtype=paddle_quantum.get_dtype())
    # Fix the dimensions of network
    net = Circuit(N)
    net.universal_two_qubits([0, 1])

    # Use Adagrad optimizer
    opt = paddle.optimizer.Adagrad(learning_rate=LR, parameters=net.parameters())

    # Optimization iterations
    for itr in range(ITR):
        U = net.unitary_matrix()
        # Run forward propagation to calculate loss function and obtain energy spectrum
        loss, rho_tilde = loss_func(U, rho, sigma)
        rho_tilde_np = rho_tilde.numpy()

        # In dynamic graph, run backward propagation to minimize loss function
        loss.backward()
        opt.minimize(loss)
        opt.clear_grad()

        # Print results
        if itr % 10 == 0:
            print('iter:', itr, 'loss:', '%.4f' % loss.numpy()[0])

    return rho_tilde_np


def main():

    D = [0.5, 0.3, 0.1, 0.1]

    rho, sigma = generate_rho_sigma()

    rho_tilde_np = Paddle_VQSD(rho, sigma)

    print("The estimated spectrum is:", numpy.real(numpy.diag(rho_tilde_np)))
    print('The target spectrum is:', D)


if __name__ == '__main__':
    main()
