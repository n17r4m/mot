import inspect
import functools

def store_args(method):
    """Stores provided method args as instance (self) attributes."""
    # https://stackoverflow.com/a/10324872/5357876
    argspec = inspect.getargspec(method)
    defaults = dict(zip( argspec.args[-len(argspec.defaults):], argspec.defaults ))
    arg_names = argspec.args[1:]
    @functools.wraps(method)
    def wrapper(*positional_args, **keyword_args):
        self = positional_args[0]
        # Get default arg values
        args = defaults.copy()
        # Add provided arg values
        list(map( args.update, ( zip(arg_names, positional_args[1:]), keyword_args.items() ) ))
        # Store values in instance as attributes
        self.__dict__.update(args)
        return method(*positional_args, **keyword_args)

    return wrapper