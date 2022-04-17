class ExpiredJwtToken(Exception):
    """JWT token过期"""


class ExpiredJwtRefreshToken(Exception):
    """刷新JWT token过期"""


class InvalidatedJwtRefreshToken(Exception):
    """刷新JWT token无效"""


class LoginFailed(Exception):
    """登录失败"""


class EmailAlreadyTaken(Exception):
    def __init__(self, msg="email already taken", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        self.field = "email"


class UsernameAlreadyTaken(Exception):
    def __init__(self, msg="username already taken", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        self.field = "username"


class InvalidUsername(Exception):
    def __init__(self, msg="Username is invalid", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
