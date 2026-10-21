def choose(a, b, c):
    # 返回 a、b、c 中首个非 None 的值；若全部为 None，则返回 None。
    return next((value for value in (a, b, c) if value is not None), None)
