import multiindex


class TestIdTime(object):
    def __init__(self, id, time):
        self.time = time
        self.id = id
        

def to_dict(obj, classkey=None):
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__"):
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value, classkey))
                     for key, value in obj.__dict__.iteritems()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj

def test():
    transactions = IndexedList()
    transactions.add_unique_index('id')
    transactions.add_index('time')

    transactions.append(TestIdTime(0, 553456670000007)) # Removed. will be removed by pk
    transactions.append(TestIdTime(1, 123456670000008)) # Stays.   less than slice start
    transactions.append(TestIdTime(2, 123456670000009)) # Stays.   will be replaced
    transactions.append(TestIdTime(7, 123456670000009)) # Removed. removed by slice
    transactions.append(TestIdTime(3, 123456680000000)) # Removed. same as 7th
    transactions.append(TestIdTime(4, 123456680000001)) # Stays.   larger than slice end
    transactions.append(TestIdTime(5, 123456680000002)) # Stays.   same as 4th
    sixth = TestIdTime(6, 123456680000003)              # Removed. by remove_item
    transactions.append(sixth)
    transactions.append(TestIdTime(8, 123456680000003)) # Removed. by remove_unique

    errors = []

    transactions.replace('id', 2, TestIdTime(2, 123456680000009))

    print('removed:')
    print(to_dict(transactions.remove_slice('time', 123456670000009, 123456680000000, True)))
    print(to_dict(transactions.pop(0)))
    print(to_dict(transactions.pop_unique('id', 8)))
    print(to_dict(transactions.pop_item(sixth)))

    for i in range(transactions.get_max_pk() + 1):
        try:
            fail = transactions.get_by('id', i)

        except KeyError:
            if i in [1, 2, 4, 5]:
                errors.append("id({}) should not be removed".format(i))

        else:
            if i in [0, 3, 6, 7, 8]:
                errors.append("{} should be removed".format(to_dict(fail)))

    if len(errors) > 0:
        print('\n'.join(errors))
        return len(errors)

    transactions.append(TestIdTime(10, 553456670000007)) # Removed. will be removed by pk
    transactions.append(TestIdTime(11, 123456670000008)) # Stays.   less than slice start
    transactions.append(TestIdTime(12, 123456670000009)) # Stays.   will be replaced
    transactions.append(TestIdTime(17, 123456670000009)) # Removed. removed by slice
    transactions.append(TestIdTime(13, 123456680000000)) # Removed. same as 7th
    transactions.append(TestIdTime(14, 123456680000001)) # Stays.   larger than slice end
    transactions.append(TestIdTime(15, 123456680000002)) # Stays.   same as 4th

    assert 11 == len(transactions)
    transactions.pop_front('time')
    assert 10 == len(transactions)
    transactions.pop_front('time')
    assert 9 == len(transactions)
    outnumbers = map(to_dict, transactions.pop_outnumbers('time', 3))
    assert 6 == len(outnumbers)
    print(outnumbers)
    assert 3 == len(transactions)
    outnumbers = map(to_dict, transactions.pop_outnumbers('time', 4))
    assert 0 == len(outnumbers)
    assert 3 == len(transactions)


if __name__=='__main__':
    test()
