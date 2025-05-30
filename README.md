# Alphastroid

## Description

Alphastroid is a Python-based arcade-style space shooter game built with Pygame.  
Pilot your ship through waves of letter-shaped asteroids, shoot them down, and survive as long as you can!

## How to Run

1. Make sure you have Python 3 installed.  

2. Install Pygame by running:
```python
pip install pygame
```
3. Run the game:
```python
python alphastroid_code.py
```
4. Enjoy!

---

## Files

- `alphastroid_code.py` – Main game code  
- `redset-nebula.png` – Background image  
- `Comfortaa-Regular.ttf` – Font used for game text  

---

## Credits

### Websites Referenced

- https://docs.python.org/3/library/math.html
- http://programarcadegames.com/python_examples/f.php?file=text_rotate.py
- https://berbasoft.com/simplegametutorials/pygamezero/asteroids/
- https://www.reddit.com/r/gamedev/comments/1gqmunz/frame_rate_dependent_vs_time_scale_dependent_games/
- https://www.w3schools.com/python/ref_math_hypot.asp
- https://www.geeksforgeeks.org/python-string-ascii_letters/
- https://www.w3schools.com/python/ref_func_abs.asp
- https://stackoverflow.com/questions/30030659/in-python-what-is-the-difference-between-random-uniform-and-random-random
- https://www.reddit.com/r/pygame/comments/1995czw/anyone_know_why_i_keep_getting_this_error_and/
- https://webflow.com/blog/parallax-scrolling
- https://www.reddit.com/r/pygame/comments/15xiccm/how_do_i_record_a_single_input_instead_of_many/
- https://www.w3schools.com/html/html_colors_rgb.asp
- https://www.pygame.org/docs/ref/surface.html
- https://www.reddit.com/r/pygame/comments/196v4o8/what_is_pygamesrcalpha/
- https://stackoverflow.com/questions/33630420/pygame-is-there-a-way-to-make-screen-layers
- https://wallpapers.com/nebula-background
- https://stackoverflow.com/questions/10473930/how-do-i-find-the-angle-between-2-points-in-pygame
- https://pandas.pydata.org/docs/development/contributing_docstring.html

### Explanation of Use

- Used Python’s `math` module for trigonometric functions.
- Used `pygame.transform.rotate()` for rotating the ship and text.
- Applied trigonometry to ship movement.
- Learned how to warp an object if it exits the screen using the same website.
- Took advice from a forum to make the game framerate independent.
- Incorporated `math.hypot()` for distance calculations.
- Incorporated `string.ascii_letters` from the `string` module for handling letters.
- Incorporated `abs()` for absolute values.
- Incorporated `random.uniform()` for randomness.
- Used a forum to fix an error related to importing fonts.
- Inspired by a website to create a parallax effect in the game.
- Took advice from a forum to record a single input instead of many when holding down a key.
- Incorporated the RGBA color model (4th property is transparency).
- Used Python docs and forums to help fade out elements using `SRCALPHA()`.
- Added multiple background layers following advice from a website.
- Downloaded background image from a wallpapers website.
- Incorporated `atan2` math function for angle calculations.
- Used pandas documentation to write proper docstrings for functions.

Feel free to reach out if you have any questions or want to contribute!