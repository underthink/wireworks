# Wireworks

Attach things to other things with wire for fun, profit, and decoupled python applications.

## Whassat?

A way of wiring components of a Python application together using event dispatch. Event receivers don't need to care 
about dispatchers, dispatchers don't have to worry about receivers. Dispatches can happen synchronously or 
asynchronously using a threadpool. All handled with nice single function/method decorations.

## What state is it in?

'In progress' is a very generous description of it's current state. It's missing a couple of things like features,
comprehensive documentation or tests, examples, real-world use, and a feel-good, can-do attitude. But it does have
that 'new project' smell you get with half-finished github projects!

## Sounds good! How do I use it?

With large amounts of optimism.

The library doesn't *really* have any external dependencies. It does use the concurrent.futures package found in 
Python 3.2 - if you're still stuck on Python 2.7 then there is a package containing a backport of that module named 
`futures` that works well enough.

Aside from that, it should work on Python 2.7+. Maybe even Python 2.6. I should check that really.

The API currently looks a little bit like:

    from wireworks.registry import Registry
    
    my_registry = Registry()
    
    
    @my_registry.wire('printstuff.normal')
    function invoke_me(arg1):
        print(arg1)
    
    @my_registry.wire('printstuff.withexclaimationmarks')
    function invoke_me(arg1):
        print(str(arg1) + "!")
    
    @a.wire_class_instances
    class MyClass(object):
        def __init__(self, name):
            self._name = name
            
        @a.wire_instance_method("printstuff.instance")
        def instance_method(self, arg1):
            print(str(arg1) + " says instance " + self._name)
            
Then you can do stuff like:
    
    >>> dispatcher = a.with_filter("printstuff.*")
    >>> def inner():
    >>>     inst = MyClass("first")
    >>>     dispatcher.call("behind you, a three headed monkey")
    >>>
    >>> inner()
    behind you, a three headed monkey
    behind you, a three headed monkey!
    behind you, a three headed monkey says instance first
    >>> second_inst = MyClass("second")
    >>> dispatcher.call("you fight like a dairy farmer")
    you fight like a dairy farmer
    you fight like a dairy farmer!
    you fight like a dairy farmer says instance second

Points to note:

 * By default, references are stored weakly, and when the original drops out of scope, it's automatically removed
   from the registry. That's what happened to `inst` in the example above.
 * The `dispatcher` object allows you to perform a live filter on the registry, as well as control how the methods
   are executed (ie what kind of executor to use).
 * The `call` method on the dispatcher returns an Event, which holds Futures for all the methods that are executing.
   It doesn't let you do anything particularly clever with them at the moment - I direct you to the section above about
   project state.

## Who's to blame?

Me! I'm rob at wireworks.endless.email.
