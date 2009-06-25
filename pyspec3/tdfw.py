# -*- coding: utf-8 -*-

"""Commitment oriented architecture framework implementations.

This is my experimental idea.

In Hollywood's raw, object B doesn't know when it called(System A).

A -> B

In This framework, it has different philosophy(System B).

A ... I'm hungry
  B ... Yes! Have a humbarger. Here you are!

System A is allopoietic and system B is autopoietic(but it has no special
features to generate copies). All objects in system B behave distributed
autonomously. Its object knows boundary between itself and outer world.
It knows what it can do and when it should work. In Hollywood's raw,
It knows what it can do but it doesn't know when it should work.

This implementation's API uses metaphor of twitter(but it does not follows
people but message/event):

  class A:
    def do_something(self):
      twitter("I'm hungry")

  class B(__metaclass__=Follower):
    @following("I'm hungry")
    def give_hunberger(self, ticket):
      print("Yes! Have a humbarger. Here you are!")

Recent frameworks inject dependencies in setting up time. But all objects
in this framework don't have dependencies at any time. In fact, you should use
this mechanism between same level objects. I call it "society".
Many systems (including real world) are hierarchical society.
Any books says that 200 is the biggest members it can live in one group
without any special rules and hierarchy.
Between societies, you can use normal relationship(including Hallywoods raw).

Have fun!

This architecture inspired by Toradora!. It's Japanese nobel/cartoon.
Characters in this pieces behave to give profit for others.
They live strongly.
This story is more impressed than Takeshi Kitano's films for me.

"""

import re
import sys
import queue
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
            self.action = {action}
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
                self.action = {match.group(1)}
                self.functions[0] = self.match_action_only
            else:
                match = self._both_name_action.match(key)
                if match:
                    self.name = match.group(1)
                    if match.group(2) == "call":
                        self.action = {"entry", "exit"}
                    else:
                        self.action = {match.group(2)}
                    self.functions[0] = self.match_all
                else:
                    self.name = key
                    self.action = {"entry", "exit"}
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
    """This method is arange version of Python Cookbook 2nd 6.10"""
    __slots__ = ("_obj", "_func")
    def __init__(self, fn):
        try:
            o, f = fn.__self__, fn.__func__
        except AttributeError:
            self._obj = None
            self._func = fn
        else:
            self._obj = weakref.ref(o)
            self._func = f

    def __call__(self):
        if self._obj is None:
            return self._func
        elif self._obj() is None:
            return None
        return types.MethodType(self._func, self._obj())


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
            follwing_id, function = follower
            if not follwing_id.is_match(id_obj, ticket):
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
        if len({"entry", "exit"} & id_obj.action) == 2:
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
    return _


def expose_method(identifier):
    id_obj = Identifier(identifier)
    def _(f):
        if id_obj.action.issubset({"entry", "exit"}):
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

      class Logger(metaclass=Follower):
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

