import functools
import inspect
from objects import User
from mongoDb import db

def route_config(
    httpMethod: str = 'GET',
    jwtRequired: bool = False,
    createAccessToken: bool = False,
    successMessage: str = 'Success',
    roleAccess: str = None
):
    def decorator(func):
        # 1) Validate decorator arguments
        if httpMethod not in [
            'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'
        ]:
            raise ValueError('Invalid http method')
        if not isinstance(jwtRequired, bool):
            raise ValueError('Invalid jwtRequired value')
        if not isinstance(createAccessToken, bool):
            raise ValueError('Invalid createAccessToken value')
        if createAccessToken and func.__name__ not in [
            'loginWithEmailAndPassword', 'loginWithGoogle'
        ]:
            raise ValueError(
                'createAccessToken can only be True for login methods'
            )
        if createAccessToken and jwtRequired:
            raise ValueError(
                'createAccessToken and jwtRequired cannot be True at the same time'
            )

        # 2) Attach metadata to the function object
        func.httpMethod = httpMethod
        func.jwtRequired = jwtRequired
        func.createAccessToken = createAccessToken
        func.successMessage = successMessage
        func.roleAccess = roleAccess

        # 3) Create the call‐wrapper that runs before invoking func
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            if func.roleAccess != None:
                # Bind args/kwargs to parameter names so we can extract userId
                sig = inspect.signature(func)
                bound_args = sig.bind_partial(*args, **kwargs)
                userId = bound_args.arguments.get('userId')

                if userId is None:
                    raise ValueError(f'userId parameter is required in function {func.__name__} for role access validation')

                # Fetch user data from MongoDB
                user_data = db.read({'_id': userId}, 'Users', findOne=True)
                if not user_data:
                    raise ValueError(f'User not found')

                user = User(**user_data)
                user.checkIfAuthorized(func.roleAccess)
                    
            return func(*args, **kwargs)

        # Enforce no parameters for GET or HEAD methods
        if httpMethod in ["GET", "HEAD"]:
            sig = inspect.signature(func)
            params = [p for p in sig.parameters.values() if p.name not in ("self", "cls")]
            if len(params) > 0:
                raise ValueError(f"{func.__name__} cannot have parameters when httpMethod is GET or HEAD")

        return wrapped

    return decorator
