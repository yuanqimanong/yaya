def choose(a, b, c):
    # 按 a、b、c 顺序返回首个非 None 的值；全部为 None 时返回 None。
    return next((value for value in (a, b, c) if value is not None), None)
