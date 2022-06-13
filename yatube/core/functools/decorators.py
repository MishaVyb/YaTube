
import time
from functools import wraps


def time_check(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = round(time.time() - start_time, 3)
        print(f'Время выполнения функции {func.__name__}: {execution_time} с.')
        return result

    return wrapper


def cache_args(func, max_count=10):
    cache = {}
    # {
    # __name__ : [
    #            {'args': .., 'kwargs': .., 'result': .., 'count': ..},
    #           ..]
    # }

    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        if name in cache:
            for current in cache[name]:
                if current['args'] == args and current['kwargs'] == kwargs:
                    if current['count'] < max_count:
                        # все условия выполнены, обратимся к кэшу
                        current['count'] += 1
                        return current['result']
                    else:
                        # максимальное кол-во вызовов
                        # обнулим рузельтаты в кеше для данных args/kwargs
                        del current
                        break
                else:
                    # данные входные параметры не совпали, ищшем дальше
                    pass
        else:
            # новая функция, добавим ее в словарь
            cache[name] = []
        # вызов исходной функции
        if args and kwargs:
            result = func(*args, **kwargs)
        elif kwargs:
            result = func(**kwargs)
        elif args:
            result = func(*args)
        else:
            result = func()
        # дополним список новым результатом
        cache[name].append(
            {
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'count': 1
            }
        )
        return result
    return wrapper
