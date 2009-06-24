# -*- coding: utf-8 -*-

import re
import new
import sys
import Queue as queue
import types
import weakref
import threading


def _dummy(ticket):
    """Dummy guard condition function.

    It always matches.

    @param ticket: passed values from expositions.
    @type  ticket: Ticket object.
    @return: whether follower should be called or not.
    @rtype : boolean.
    """
    return True


class Identifier(object):
    """Event naming identifier.

    identifier is built by string.
    It supports wildcard.

    "sample:*" => match any action in "sample"
    "*:entry" => match any "entry" messsge
    "sample" => match with "sample:entry" and "sample:exit" message

    @future: including URI(for external followable node)
    """
    __slots__ = ("name", "action", "functions")
    _both_name_action = re.compile(r"(.*):(.*)")
    _every_action = re.compile(r"(.*):\*")
    _every_name = re.compile(r"\*:(.*)")

    def __init__(self, key_or_identifier, action=None, guard_condition=_dummy):
        self.functions = [None, None]
        if action is not None:
            self.name = key_or_identifier.name
            self.action = set([action])
            self.functions[0] = self.match_all
            return
        key = key_or_identifier
        match = self._every_action.match(key)
        if match:
            self.name = match.group(1)
            self.action = None
            self.functions[0] = self.match_name_only
        else:
            match = self._every_name.match(key)
            if match:
                self.name = None
                self.action = set([match.group(1)])
                self.functions[0] = self.match_action_only
            else:
                match = self._both_name_action.match(key)
                if match:
                    self.name = match.group(1)
                    if match.group(2) == "call":
                        self.action = set(["entry", "exit"])
                    else:
                        self.action = set([match.group(2)])
                    self.functions[0] = self.match_all
                else:
                    self.name = key
                    self.action = set(["entry", "exit"])
                    self.functions[0] = self.match_all
        self.functions[1] = guard_condition

    def __str__(self):
        name = "*" if self.name is None else self.name
        action = "*" if self.action is None else ",".join(sorted(self.action))
        return "<tdfw.Identifier object at %d: id=%s:%s>" % (
            id(self), name, action)

    @staticmethod
    def match_all(lhs, rhs):
        return (lhs.name == rhs.name) and (lhs.action & rhs.action)

    @staticmethod
    def match_name_only(lhs, rhs):
        return lhs.name == rhs.name

    @staticmethod
    def match_action_only(lhs, rhs):
        return lhs.action & rhs.action

    def is_match(self, expose_identifier, ticket=None):
        if self.functions[0](self, expose_identifier):
            return self.functions[1](ticket)
        return False

    def available_for_exposition(self):
        return self.name and self.action


class cond(object):
    def __init__(self, identifier, guard_condition=_dummy):
        self.targets = [Identifier(identifier, guard_condition=guard_condition)]

    def __and__(self, rhs):
        newtarget = target(None, None)
        newtarget.targets = self.targets + rhs.targets
        return newtarget


def _get_attributes(instance, typeobj):
    """Helper generator to implement TDFW.

    It returns match objects.
    """
    for key in dir(instance):
        if key.startswith("__"):
            continue
        value = getattr(instance, key)
        if type(value) == typeobj:
            yield value


class _weakmethod_ref(object):
    """This method wrapper comes from Python Cookbook 2nd 6.10"""
    __slots__ = ("_obj", "_func", "_clas")
    def __init__(self, fn):
        try:
            o, f, c = fn.im_self, fn.im_func, fn.im_class
        except AttributeError:
            self._obj = None
            self._func = fn
            self._clas = None
        else:
            if o is None:
                self._obj = None
            else:
                self._obj = weakref.ref(o)
            self._func = f
            self._clas = c

    def __call__(self):
        if self._obj is None:
            return self._func
        elif self._obj() is None:
            return None
        return new.instancemethod(self._func, self._obj(), self._clas)


class _dummy_method_ref(object):
    __slots__ = ("_func",)
    def __init__(self, fn):
        self._func = fn

    def __call__(self):
        return self._func



class InvalidExpositionName(Exception): pass


class TDFramework(object):
    _followers = {}
    _expositions = set()

    def __init__(self):
        pass

    def get_valid_followers(self):
        for name, followers in self._followers.items():
            for id_obj, function_wrapper, condition in followers:
                function = function_wrapper()
                if function is not None:
                    yield id_obj, function

    def get_valid_expositions(self):
        for id_obj, function_wrapper in self._expositions:
            function = function_wrapper()
            if function is not None:
                yield id_obj, function

    def regist_exposition(self, id_obj, function):
        self._expositions.add((id_obj, function))

    def regist_follower(self, id_obj, function):
        followers = self._followers.setdefault(id_obj.name, [])
        followers.append((id_obj, function))

    def twitter(self, id_obj, args, kwargs, counter=100):
        ticket = Ticket(id_obj, args, kwargs, counter)
        for follower in self._followers.get(id_obj.name, []):
            following_id, function = follower
            if not following_id.is_match(id_obj, ticket):
                continue
            if function() is None:
                continue # あとで削除
            if ThreadPool.empty():
                function()(ticket)
            else:
                ThreadPool.request_work(function(), ticket)


class ThreadPool(object):
    _qin = queue.Queue()
    _qerr = queue.Queue()
    _pool = []

    @classmethod
    def _report_error(cls):
        cls._qerr.put(sys.exc_info()[:2])

    @staticmethod
    def _get_all_from_queue(Q):
        try:
            while True:
                yield Q.get_nowait()
        except queue.Empty:
            raise StopIterator

    @classmethod
    def do_work_from_queue(cls):
        while True:
            command, target_method, ticket = cls._qin.get()
            if command == "stop":
                break
            try:
                if command == "process":
                    target_method(ticket)
                else:
                    raise ValueError("Unknown command %r" % command)
            except:
                cls._report_error()

    @classmethod
    def make_thread_pool(cls, number):
        if number < 0:
            raise ValueError("'number' should be bigger than 0.")
        number -= len(cls._pool)
        if number > 0:
            for i in range(number):
                new_thread = threading.Thread(target=cls.do_work_from_queue)
                new_thread.setDaemon(True)
                cls._pool.append(new_thread)
                new_thread.start()
        elif number < 0:
            number = abs(number)
            for i in range(number):
                cls.request_work(None, None, "stop")

    @classmethod
    def empty(cls):
        return len(cls._pool) == 0

    @classmethod
    def clear_thread_pool(cls):
        alive_list = []
        for thread in cls._pool:
            if thread.isAlive():
                alive_list.append(thread)
        cls._pool = alive_list


    @classmethod
    def request_work(cls, target_function, ticket, command="process"):
        cls._qin.put((command, target_function, ticket))

    @classmethod
    def get_all_errors(cls):
        return cls._get_all_from_queue(cls._qerr)

    @classmethod
    def stop_thread_pool(cls):
        for i in range(len(cls._pool)):
            cls.request_work(None, None, "stop")
        for existing_thread in cls._pool:
            existing_thread.join()
        del cls._pool[:]


class OpenMethodAttribute(object):
    """This class is attached to exposition/following functions/methods.

    After initialization, this shows any information to draw connections.

    @sa exposition
    @sa following
    @sa following_method
    """
    __slots__ = ("expositions", "followers", "is_init")
    attribute_name = "__exposition_information"
    def __init__(self):
        self.expositions = []
        self.followers = []
        self.is_init = False

    @classmethod
    def add_follower(cls, id_obj, function):
        attribute = cls._set_open_method_attribute(function)
        attribute.followers.append(id_obj)

    @classmethod
    def add_exposition(cls, id_obj, function):
        attribute = cls._set_open_method_attribute(function)
        attribute.expositions.append(id_obj)

    @classmethod
    def _set_open_method_attribute(cls, function):
        attribute = getattr(function, cls.attribute_name, None)
        if attribute is None:
            attribute = cls()
            setattr(function, cls.attribute_name, attribute)
        return attribute



def expose(identifier):
    id_obj = Identifier(identifier)
    def _(f):
        if isinstance(f, types.FunctionType):
            if len(set(["entry", "exit"]) & id_obj.action) == 2:
                _tdfw.regist_exposition(id_obj, _dummy_method_ref(f))
                def __(*args, **kwargs):
                    _tdfw.twitter(Identifier(id_obj, "entry"), args, kwargs)
                    f(*args, **kwargs)
                    _tdfw.twitter(Identifier(id_obj, "exit"), args, kwargs)
                return __
            elif "exit" in id_obj.action:
                _tdfw.regist_exposition(id_obj, _dummy_method_ref(f))
                def __(*args, **kwargs):
                    f(*args, **kwargs)
                    _tdfw.twitter(Identifier(id_obj, "exit"), args, kwargs)
                return __
            elif "entry" in id_obj.action:
                _tdfw.regist_exposition(id_obj, _dummy_method_ref(f))
                def __(*args, **kwargs):
                    _tdfw.twitter(Identifier(id_obj, "entry"), args, kwargs)
                    f(*args, **kwargs)
                return __
            else:
                _tdfw.regist_exposition(id_obj, _dummy_method_ref(f))
            return f
        else:
            if id_obj.action.issubset(set(["entry", "exit"])):
                OpenMethodAttribute.add_exposition(id_obj, f)
                def __(*args, **kwargs):
                    _tdfw.twitter(Identifier(id_obj, "entry"), args, kwargs)
                    f(*args, **kwargs)
                    _tdfw.twitter(Identifier(id_obj, "exit"), args, kwargs)
                return __
            elif "exit" in id_obj.action:
                OpenMethodAttribute.add_exposition(id_obj, f)
                def __(*args, **kwargs):
                    f(*args, **kwargs)
                    _tdfw.twitter(Identifier(id_obj, "exit"), args, kwargs)
                return __
            elif "entry" in id_obj.action:
                OpenMethodAttribute.add_exposition(id_obj, f)
                def __(*args, **kwargs):
                    _tdfw.twitter(Identifier(id_obj, "entry"), args, kwargs)
                    f(*args, **kwargs)
                return __
            else:
                OpenMethodAttribute.add_exposition(id_obj, f)
            return f
    return _


expose_method = expose


def following(identifier, guard_condition=_dummy):
    id_obj = Identifier(identifier, guard_condition=guard_condition)
    def _(f):
        _tdfw.regist_follower(id_obj, _dummy_method_ref(f))
        return f
    return _


def following_method(identifier, guard_condition=_dummy):
    """This decorator is used for lazy instance method registration.

    @sa Follower
    @sa following
    """
    id_obj = Identifier(identifier, guard_condition=guard_condition)
    def _(f):
        OpenMethodAttribute.add_follower(id_obj, f)
        return f
    return _


class Follower(type):
    """Metaclass for definition of follower instance methods.

    use like this:

      class Logger(object):
          __metaclass__=Follower
          @following_method("function", "call")
          def log_function_call(self, ticket):
              ...

          @classmethod
          @following_classmethod("error", "raised")
          def show_error(cls, ticket):
              ...

          @staticmethod
          @following("thread", "created")
          def log_thread(ticket):
              ...
    """
    def __new__(cls, name, bases, dict):
        """Create exposition point for classmethod."""
        newtype = type.__new__(cls, name, bases, dict)
        for method in _get_attributes(newtype, types.MethodType):
            attribute = getattr(method, OpenMethodAttribute.attribute_name, None)
            if attribute is None:
                continue
            if method.im_self is None:
                continue
            for id_obj in attribute.followers:
                _tdfw.regist_follower(id_obj, _weakmethod_ref(method))
            for id_obj in attribute.expositions:
                _tdfw.regist_exposition(id_obj, _weakmethod_ref(method))
            attribute.is_init = True
        return newtype

    def __call__(cls, *args):
        """Create exposition point for instancemethod."""
        instance = type.__call__(cls, *args)
        for method in _get_attributes(instance, types.MethodType):
            attribute = getattr(method, OpenMethodAttribute.attribute_name, None)
            if attribute is None:
                continue
            if attribute.is_init:
                continue
            for id_obj in attribute.followers:
                _tdfw.regist_follower(id_obj, _weakmethod_ref(method))
            for id_obj in attribute.expositions:
                _tdfw.regist_exposition(id_obj, _weakmethod_ref(method))
        return instance


class Ticket(object):
    def __init__(self, id_obj, args, kwargs, counter):
        self._id_obj = id_obj
        self._args = args
        self._kwargs = kwargs
        self._counter = counter
        self.__dict__.update(kwargs)
        self.__dict__["args"] = args

    @property
    def name(self):
        return self._id_obj._name

    @property
    def action(self):
        return self._id_obj._action

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def twitter(self, id_obj, **kwargs):
        _tdfw.twitter(id_obj, kwargs, self._counter-1)

    def apply(self, func):
        """Utility method to enease method call deligation.

        You can use like this:
          @exposition("result", "show")
          def show_result(score):
              print("my score:", score)
              twitter("result", "show", username="shibu", score=score) # get 2 kwparams

          def log(username, score): # same params with exposition point.
              ...

          @following("result", "show")
          def log_score_exposition(ticket):
              ticket.apply(log) # use this!

        """
        return func(**self.kwargs)


_tdfw = TDFramework()


def set_multiplicity(number):
    if number != 0:
        ThreadPool.make_thread_pool(number)
    else:
        ThreadPool.clear_thread_pool()


def show_expositions():
    methods = []
    for id_obj, function_wrapper in _tdfw.get_valid_expositions():
        for action in id_obj.action:
            methods.append("%s:%s" % (id_obj.name, action))
    return sorted(set(methods))


def show_followers():
    methods = []
    for id_obj, function_wrapper in _tdfw.get_valid_followers():
        for action in id_obj.action:
            methods.append("%s:%s" % (id_obj.name, action))
    return sorted(set(methods))


def show_network():
    network = {}
    nodes = []
    edges = []
    classobjs = set()

    nodetype = {"class":{"shape":"box3d", "bgcolor":"#C1E4FF",
                         "pencolor":"#358ACC"},
                "joint":{"shape":"none"}}

    for name, action, method in _tdfw.get_valid_expositions():
        key = (name, action)
        net = network.setdefault(key, {"follower":[], "exposition":[]})
        if isinstance(method, types.MethodType):
            classobjs.add(method.__self__.__class__)
            net["exposition"].append(id(method.__self__.__class__))
        else:
            net["exposition"].append(None)

    for name, action, method in _tdfw.get_valid_followers():
        key = (name, action)
        net = network.setdefault(key, {"follower":[], "exposition":[]})
        if isinstance(method, types.MethodType):
            classobjs.add(method.__self__.__class__)
            net["follower"].append(id(method.__self__.__class__))
        else:
            net["follower"].append(None)

    for classobj in classobjs:
        nodes.append(["class", id(classobj), classobj.__name__])

    for key in network:
        followers = network[key]["follower"]
        expositions = network[key]["exposition"]
        if len(followers) == 1 and len(expositions) == 1:
            edges.append([expositions[0], followers[0],
                          {"label": "%s:%s"%key}])
        else:
            nodes.append(["joint", id(classobj), "%s:%s"%key])
            for exposition in expositions:
                edges.append([exposition, id(classobj),{"label":""}])
            for follower in followers:
                edges.append([id(classobj), follower,{"label":""}])
    result = ["digraph {"]

    for typename, objid, label in nodes:
        params = ['label="%s"' % label]
        params += ['%s="%s"' % item for item in nodetype[typename].items()]
        result.append("  %s [%s];" % (objid, ", ".join(params)))
    for start, end, params in edges:
        param_str = ['%s="%s"' % item for item in params.items()]
        result.append("  %s -> %s [%s];" % (start, end, ", ".join(param_str)))
    result.append("}")
    return "\n".join(result)


def twitter(identifier, *args, **kwargs):
    _tdfw.twitter(Identifier(identifier), args, kwargs)


fire = twitter
notify = twitter
