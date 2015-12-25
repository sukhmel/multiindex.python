#!/usr/bin/python -utt

from sortedcontainers import SortedList, SortedDict
from operator import itemgetter, attrgetter


class IndexedList(object):
    def __init__(self, hash=None, *args, **kwargs):
        self.pk = 0
        self.primary = SortedDict()
        self.indices = {}
        self.uniques = {}
        self.keys = {}
        self.hash = (lambda x: x) if hash is None else hash
        self.load = kwargs.get('load', 1000)

    def add_unique_index(self, name, key=None):
        if key is None:
            key = attrgetter(name)

        key_getter = lambda pair: self.hash(key(pair[1]))

        self.uniques[name] = SortedDict(self.load)
        self.keys[name] = key_getter

    def add_index(self, name, key=None):
        if key is None:
            key = attrgetter(name)

        self.indices[name] = SortedList(key=lambda pair: key(pair[1]), load=self.load)

    def append(self, item):
        pair = (self.pk, item)
        self.primary[self.pk] = item
        self.pk += 1

        for name, key_getter in self.keys.iteritems():
            self.uniques[name][key_getter(pair)] = pair
        for name in self.indices:
            self.indices[name].add(pair)

    def replace(self, key, val, item):
        old_pair = self.uniques[key][self.hash(val)]
        new_pair = (old_pair[0], item)

        for key, key_getter in self.keys.iteritems():
            self.uniques[key][key_getter(old_pair)] = new_pair

        for key in self.indices:
            self.indices[key].remove(old_pair)
            self.indices[key].add(new_pair)

        self.primary[old_pair[0]] = item

    def insert_or_replace(self, key, val, item):
        if self.hash(val) in self.uniques[key]:
            self.replace(key, val, item)
        else:
            self.append(item)

    def pop_all(self):
        result = []
        for position in self.primary:
            result.append(self.pop(position))

        return result

    def pop(self, position):
        item = self.primary[position]
        del self.primary[position]
        for index, key_getter in self.keys.iteritems():
            del self.uniques[index][key_getter((position, item))]
        for index in self.indices:
            self.indices[index].remove((position, item))
        return item

    def remove(self, position):
        self.pop(position)

    def pop_item(self, item):
        pk = None
        for key, key_getter in self.keys.items():
            if not pk:
                pair = self.uniques[key][key_getter((None, item))]
                pk = pair[0]
                return self.pop(pk)

    def remove_item(self, item):
        self.pop_item(item)

    def remove_unique(self, index, key):
        self.pop_unique(index, key)

    def pop_unique(self, index, key):
        item = self.uniques[index][self.hash(key)]
        return self.pop(item[0])

    def remove_slice(self, index, begin, end, include_last=True):
        self.pop_slice(index, begin, end, include_last)

    def pop_outnumbers(self, index, keep, keep_from_beginning=False):
        """
        Remove all elements but given `keep` amount from the end.
        :param index: index name to sort by
        :param keep: amount of elements to leave
        :param keep_from_beginning: True if we need to leave `keep` first elements instead of `keep` last ones
        """
        target = self.indices[index][keep:] if keep_from_beginning else self.indices[index][:-keep]
        positions = map(itemgetter(0), target)
        removed = map(self.pop, positions)
        return removed

    def pop_slice(self, index, begin, end, include_last=True, limit=0):
        """
        Remove slice of elements by non-unique key
        :param index: index name to slice
        :param begin: elements (>= begin) will be removed
        :param end: elements (<[=] end) will be removed
        :param include_last: inclusive last end
        :param report: False if should not return list of removed objects
        :return: removed object in list
        """
        items = map(itemgetter(0), self.get_slice_items(index, begin, end, include_last, limit))
        removed = map(self.pop, items)
        return removed

    def pop_front(self, index):
        element = self.indices[index][0]
        self.remove(element[0])
        return element

    def __getitem__(self, item):
        return self.primary[item][1]

    def __iter__(self):
        return self.primary.itervalues()

    def __len__(self):
        return len(self.primary)

    def get_max_pk(self):
        return self.pk

    def get_by(self, index, key):
        if index in self.uniques:
            return self.uniques[index][self.hash(key)][-1]
        elif index in self.indices:
            return self.indices[index][key][-1]
        else:
            raise KeyError("{} isn't indexed".format(index))

    def get_slice_items(self, index, begin, end, include_last=True, limit=0):
        start = self.indices[index].bisect_key_left(begin)
        finish = self.indices[index].bisect_key_right(end) if include_last else self.indices[index].bisect_key_left(end)
        return self.indices[index][start:finish if limit == 0 else min(finish, start+limit)]

    def get_slice(self, index, begin, end, include_last=True):
        """
        Get slice of elements by non-unique key
        :param index: index name to slice
        :param begin: elements (>= begin) will be removed
        :param end: elements (<[=] end) will be removed
        :param include_last: inclusive last end
        :return: slice in list
        """
        return map(itemgetter(1), self.get_slice_items(index, begin, end, include_last))

    def try_get_by(self, index, key, default=None):
        try:
            return self.get_by(index, key)
        except KeyError:
            return default

    def iter_by(self, index):
        if index in self.uniques:
            target = self.uniques[index]
        elif index in self.indices:
            target = self.indices[index]
        else:
            raise KeyError("{} isn't indexed".format(index))

        def gen():
            it = target.itervalues()
            while True:
                el = it.next()
                if not isinstance(el, tuple):
                    raise StopIteration
                yield el[1]

        return gen()

    def iter_reverse_by(self, index):
        if index in self.uniques:
            target = self.uniques[index]
        elif index in self.indices:
            target = self.indices[index]
        else:
            raise KeyError("{} isn't indexed".format(index))

        def gen():
            it = target.__reversed__()
            while True:
                ukey = it.next()
                el = self.uniques[index][ukey]
                if not isinstance(el, tuple):
                    continue
                yield el[1]

        return gen()

    def iterate(self, index, begin, end):
        start = self.indices[index].bisect_key_left(begin)
        finish = self.indices[index].bisect_key_right(end)

        def gen():
            it = iter(self.indices[index][start:finish])
            while True:
                el = it.next()
                if not isinstance(el, tuple):
                    raise StopIteration
                yield el[1]

        return gen()
