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
The source file of the basic class for the quantum gates.
"""

import paddle_quantum


class Gate(paddle_quantum.Operator):
    r"""Basis class for quantum gates.

    Args:
        depth: Number of layers. Defaults to 1.
        backend: Backend on which the gates are executed. Defaults to None.
        dtype: Type of data. Defaults to None.
        name_scope: Prefix name used by the layer to name parameters. If prefix is "my_layer", parameter name in
            MyLayer can be "my_layer_0.w_n", where "w" is the parameter base name and "n" is an unique suffix
            auto-generated. If ``None``, prefix name will be snake cased class name. Defaults to ``None``.
    """
    def __init__(
            self, depth: int = 1, backend: paddle_quantum.Backend = None, dtype: str = None, name_scope: str = None
    ):
        super().__init__(backend, dtype, name_scope)
        self.depth = depth

    def forward(self, *inputs, **kwargs):
        raise NotImplementedError

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if isinstance(value, paddle_quantum.Operator):
            if value.backend is None:
                value.backend = paddle_quantum.get_backend() if self.backend is None else self.backend
            if value.dtype is None:
                value.dtype = paddle_quantum.get_dtype() if self.dtype is None else self.dtype
