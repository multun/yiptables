# Yiptables, a yaml to iptables-restore tranpiler
# Copyright (C) 2017 Victor Collod <victor.collod@prologin.org>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from meta import YipSyntaxError

simple_format = re.compile(r'^{([^{} \t()\*\\=/%+-]+)}$')


def yip_stringize(e):
    if not any(map(lambda x: isinstance(e, x), (int, str))):
        raise YipSyntaxError(e, f'Element is not a string: {e}')
    return str(e)


def yip_get_single_var(scope, string):
    if not isinstance(string, str):
        return None
    match = re.match(simple_format, string)
    if match:
        vname = match.group(1)
        lookup_res = scope.get(vname)
        if lookup_res is None:
            raise YipSyntaxError(string, f'Undefined variable `{vname}`')
        return lookup_res
    return None


def yip_str_format(scope, string):
    res = yip_get_single_var(scope, string)
    return res if res else string.format(**scope)


def yip_dict_format(scope, d):
    return {k: yip_format(scope, v) for k, v in d.items()}


def yip_list_format(scope, d):
    return [yip_format(scope, v) for v in d]


def yip_format(scope, e):
    if isinstance(e, dict):
        return yip_dict_format(scope, e)
    elif isinstance(e, list):
        return yip_list_format(scope, e)
    elif isinstance(e, str):
        return yip_str_format(scope, e)
    return yip_stringize(e)


def yip_ld_iter(ld):
    if isinstance(ld, list):
        for e in ld:
            yield from yip_ld_iter(e)
    elif isinstance(ld, dict):
        yield from ld.items()
    else:
        raise YipSyntaxError(ld, f'Cannot iterate as dict on: {ld}')


def yip_flatten_iter(l):
    if isinstance(l, list):
        for e in l:
            yield from yip_flatten_iter(e)
    else:
        yield l


def yip_split(s, splitter=re.compile(r'[ \t,]+')):
    return re.split(splitter, s)


def yip_listize(e, transform=lambda x: x):
    if isinstance(e, str):
        return yip_split(e)
    if isinstance(e, list):
        return e
    return [e]


class Registrator():
    def __init__(self, fmap):
        self.fmap = fmap

    def __call__(self, *fnames):
        def assign(f):
            for fname in fnames:
                if fname in self.fmap:
                    raise YipSyntaxError(
                        fname,
                        f'feature token `{fname}` was'
                        f'used multiple times'
                    )
                self.fmap[fname] = f
            return f
        return assign
