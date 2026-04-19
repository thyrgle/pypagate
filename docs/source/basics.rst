Basics of Formulas
==================

Imagine you are working in a spreadsheet editor such as Excel. You write in a bunch of test scores and then use a formula to calculate the average of all the students. You mistakenly gave one student the wrong score. No worries, you update the score and the average is magically updated.

Now, imagine you are working with Python to do the same thing. You input the student scores in a list and calculate the mean:

.. code-block:: python

   >>> from statistics import mean
   >>> scores = [80, 85, 95, 100]
   >>> mean(scores)
   90

You then realized you need to update the score of one student, so you change the corresponding entry in ``scores`` but unlike the Excel scenario, the mean is not magically updated. Sure, you could call mean again and recalculate the new scores, but would it not be cool if you just had a variable that always updated accordingly?

-------------------------------------
Enter functional reactive programming
-------------------------------------

The core idea in this library is that the cells in Excel which contain data we manually update, and there are cells in Excel which update based on data. The cells we manually update we refer to as Terms and the cells that automatically update are referred to as Formulas.

Let us look at a small example:

.. code-block:: python

   >>> from pypagate import Term
   >>> x = Term(5)
   >>> y = x + 1
   >>> print(x.unwrap()) # (Call unwrap to get the value x currently stores)
   5
   >>> print(y.unwrap())
   6
   >>> x += 1
   >>> print(y.unwrap())
   7

``y`` magically changed even though we never touched it. This is the power of functional reactive programming (FRP).

----------------------------------
Combining FRP with Event Listeners
----------------------------------

An event listener is a construct that waits for an event to happen and then executes some code when the event does happen. pypagate gives an elegant way to make new event listeners and organize your code.

Suppose we have a ``player`` object that has a health attribute. We can develop sophisticated event listeners to fire when the ``player``'s health drops to ``0```. Observe

.. code-block:: python
   
   >>> from pypagate import Term, fire_on
   >>> class Player:
   ...     def __init__(self, health):
   ...         self.health = Term(health)
   ...
   >>> player = Player(3)
   >>> @fire_on(player.health == 0)
   >>> def game_over():
   ...     print("Game over")
   >>> player.health -= 1
   >>> player.health -= 1
   >>> player.health -= 1
   Game over

The ``fire_on`` decorator waits for a formula to evaluate to ``True`` and then fires the corresponding function. Now, we can construct sophisticated event listeners using simple formula!
