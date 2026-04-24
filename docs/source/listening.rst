Listening
=========

Unfortunately, not many APIs are made with FRP in mind. We can get around this by "listening" with the ``pypagate.source`` module, in particular we "listen" to the outside world using ``SourceMap`` objects.

---------------------
FRP in the Real World
---------------------

Consider the following `Pygame starting example: <https://pyga.me/docs/>`_

.. code-block:: python

   # Example file showing a basic pygame "game loop"
   import pygame

   # pygame setup
   pygame.init()
   screen = pygame.display.set_mode((1280, 720))
   clock = pygame.time.Clock()
   running = True

   while running:
       # poll for events
       # pygame.QUIT event means the user clicked X to close your window
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               running = False

       # fill the screen with a color to wipe away anything from last frame
       screen.fill("purple")

       # flip() the display to put your work on screen
       pygame.display.flip()

       clock.tick(60)  # limits FPS to 60

   pygame.quit()

All it does is display a simple screen filled with purple. One last important observation is that when you click the ``X`` on the window you exit the game.

Let's take a closer look at

.. code-block:: python

   for event in pygame.event.get():
       if event.type == pygame.QUIT:
           running = False

Handling all the events in a ``for``-loop ``if``-chain can get unwieldy quickly. Building on from the previous section it would make much more sense to write something like this:

.. code-block:: python

   # Example file showing a basic pygame "game loop"
   import pygame
   from pypagate import Term

   # pygame setup
   pygame.init()
   screen = pygame.display.set_mode((1280, 720))
   clock = pygame.time.Clock()
   running = Term(True)

   @fire_on(events.type == pygame.QUIT)
   def quit_game():
       running.change(False)

   while running:
       ...

The issue is ``event`` and ``event.type`` is not a ``Term`` so neither of them can be used to make ``Formula``.

-----------------------------------
Converting Existing Values to Terms
-----------------------------------

From ``pypagate.source`` we can use ``SourceMap`` to essentially take old-world values and convert them into ``Terms`` for us to use in a *reactive* fashion.

.. code-block:: python

   # Example file showing a basic pygame "game loop"
   import pygame
   from pypagate import Term
   from pypagate.source import SourceMap

   # pygame setup
   pygame.init()
   screen = pygame.display.set_mode((1280, 720))
   clock = pygame.time.Clock()
   running = Term(True)
   source = SourceMap({"quit_game": pygame.event.peek(eventtype=pygame.QUIT)})


   @fire_on(source.quit_event) # == True
   def quit_game():
       global running
       running.change(False)

   while running.unwrap():
       source.listen({"quit_event": pygame.event.peek(eventtype=pygame.QUIT)})

       # fill the screen with a color to wipe away anything from last frame
       screen.fill("purple")

       # flip() the display to put your work on screen
       pygame.display.flip()

       clock.tick(60)  # limits FPS to 60

   pygame.quit()

Importantly, ``source`` is a ``SourceMap`` that listens for the ``pygame.QUIT`` event. When ever it becomes true ``quit_game`` is executed and ``running`` is set to ``False``.

Of course, this is a bit of a toy example, but for more sophisticated events combing ``SourceMap`` objects with more sophisticated formula allow for a powerful organizational tool.

-------------------------------
Some Additional Event Listeners
-------------------------------

``global`` is generally frowned upon and it would be nice if we could get rid of it. We can by utilizing some classes and *more* event listeners. In particular, we will use ``SourceMap`` to make event listeners! There are two decorators of importance.

* ``@exec_always(source)``
* ``@exec_while(form, source)``

The first decorator ``@exec_always(source)`` executes every time the specified ``source`` calls ``.listen(...)``. The second decorator executes every time the specified ``source`` calls ``.listen(...)`` *and* it requires the formula ``form`` evaluates to ``True`` at the time ``.listen(...)`` is invoked.

Let us make ``running`` no longer a global variable by encapsulating inside of a ``Game`` class.

.. code-block:: python
   
   @dataclass
   class Game:
       running: Term = Term(False)
       events: SourceMap = SourceMap({"dt": 0, "quit_event": False})

       def run(self):
           self.running.change(True)
           while running:
               events.listen({
                   "quit_event": pygame.event.peek(eventtype=pygame.QUIT),
                   "dt": clock.tick(60)
                })
   game = Game()

Now we can ``@exec_always`` to make an update method:

.. code-block:: python

   @exec_always(game.events)
   def update():
       # We don't actually need dt.
       screen.fill("purple")
       pygame.display.flip()

And we can ``@fire_on`` like before to handle exiting the game now without the global.

.. code-block:: python
   @fire_on(game.events.quit_event)
   def quit_game():
       game.running.change(False)

Putting everything together we get:

.. code-block:: python

   from dataclasses import dataclass
   import pygame
   from pypagate import Term
   from pypagate.source import SourceMap

   # pygame setup
   pygame.init()
   screen = pygame.display.set_mode((1280, 720))
   clock = pygame.time.Clock()

   @dataclass
   class Game:
       running: Term = Term(False)
       events: SourceMap = SourceMap({"dt": 0, "quit_event": False})

       def run(self):
           self.running.change(True)
           while self.running.unwrap():
               events.listen({
                   "quit_event": pygame.event.peek(eventtype=pygame.QUIT),
                   "dt": clock.tick(60)
                })
           pygame.quit()

   game = Game()


   @fire_on(game.events.quit_event) # == True
   def quit_game():
       game.running.change(False)


   @exec_always(game.events)
   def update():
       # We don't actually need dt for this example.
       screen.fill("purple")
       pygame.display.flip()


   if __name__ == '__main__':
       game.run()
