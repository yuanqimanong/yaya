def choose(a, b, c):
    # 返回任一为真的配置。
    return next((value for value in (a, b, c) if value is not None), None)
