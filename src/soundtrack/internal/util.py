# 
# Modified from the original in the Tiramisu Discord Bot
# ------------------------------------------------------
# Copyright (c) TheKrafter, fizzdev, et al.
"""
BSD 3-Clause License

Copyright (c) 2023, RoseSMP Network et al.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from logging42 import logger
from typing import Optional

def verify_config(config: dict, example: dict, repair: Optional[bool] = True):
    """ Verify contents of `config` against `example`
    Will repair if `repair` is set to true (default True) """
    
    missing_paths = []
    def _recurse_check(config: dict, example: dict, path) -> dict:
        missing = {}
        for key in example:
            if key not in config:
                missing_paths.append(f'{path}.{key}')
                missing[key] = example[key]
            elif type(example[key]) == dict:
                recursed = _recurse_check(config[key], example[key], f'{path}.{key}')
                if recursed != {}:
                    missing[key] = recursed
        return missing
    
    def _merge(a, b, path=None, update=True):
        """ Merges dictionaries recursively,
        Credit to Andrew Cooke and Osiloke on StackOverflow: https://stackoverflow.com/a/25270947/16263200 """
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    _merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                elif isinstance(a[key], list) and isinstance(b[key], list):
                    for idx, val in enumerate(b[key]):
                        a[key][idx] = _merge(a[key][idx], b[key][idx], path + [str(key), str(idx)], update=update)
                elif update:
                    a[key] = b[key]
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    missing = _recurse_check(config, example, '')
    if missing == {}:
        logger.success(f'Config did not need repaired!')
    elif repair:
        logger.warning(f'Repairing your configuration file')
        new = _merge(config, missing)
        return new
    else:
        logger.critical(f'Your config file is missing the following options: {missing_paths}')
        return None

def auto_configure():
    pass    #TODO