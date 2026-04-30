Creating Collections of Formula
===============================

Consider we have an ``enemy`` which also has a health (like as in the ``player`` example). It might be that we need to execute a function if *any* of the ``enemy`` instances have their health drops to zero. Unfortunately, something like:

.. code-block:: python

   @fire_on(enemy.health == 0)
   def kill_enemy(enemy):
       ...

will only check (and eventually kill) one enemy. We would like to work over collections of enemies. To do so, we will add enemies to a ``Universe``. The ``Universe`` has ``Law`` objects. ``Law`` objects are similar to ``Formula`` except ``Law`` objects operate on ``Variable`` objects *instead of* ``Term`` objects. ``Variable`` objects "range" over entities of the specified ``Universe``.

Let us consider a small example to clarify the barrage of objects.

.. code-block:: python

   # Define some entities to place in our universe.
   v1, v2 = Term(0), Term(0)
   # Place them in some universe.
   U = Universe([v1, v2])
   # Now create a variable we will make a Law with.
   x = Variable(U)
   # This can be thought of as, check to see if either v1 == 1 *or* v2 == 2.
   law = (x == 1)
   # Now we will do something interesting!
   @fire_on_each(law):
   def f():
       print("Somebody became 1!")
   
   v1.change(1)
   # Prints "Somebody became 1!"
   v2.change(1)
   # Prints "Somebody became 1!"

The ``@fire_on_each(law)`` will check if a ``Law`` is satisfied. A ``Law`` is satisfied when an entity of the ``Universe`` can be substituted into a combination of variables and have the resulting ``Formula`` evaluate to ``True``. Thus, when we execute ``v1.change(1)``, we (in essence) substitute ``v1`` for ``x`` and execute ``f`` because ``x == 1 -> v1 == 1``.
