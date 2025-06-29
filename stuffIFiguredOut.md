### stuff i learned

1. property != variable
	- a variable is just data stored in memory
	- a property can be connected to a getter, setter and deleter function
2. you can remove the frame of the window and let the window stay on top
3. you can change the windows opacity
4. adding hotkeys to the application without always having a loop to check for inputs
5. pyqtSignals are OP
6. Reverse look-up lists are ridiculously fast O(n)
7. Multithreading still sucks to manage
8. You can style the whole window lol
9. The click-event system is weird as hell
10. You can add icons to a listWidget's item
11. You can add tool-tips to items in listWidgets
12. Inheritance is absolutely OP and super fun to use
13. Split the config up into individual sections. It's much easier to handle for the pc
14. You can split paths from right to left??? .rsplit()
15. Queues are super OP when you use multithreading to store data 
16. Use chunks of packages and append them to a list instead of repeatedly adding stuff. For some reason, it's much faster lol
17. Reverse look-up dicts are now the love of my life. They made the whole program like 20x faster lol
18. AVOID USING TO MANY FUNCTIONS TO CONVERT TYPES INTO ANOTHER. IT WASTES TO MUCH PROCESSING
	- When I was checking if a template/file already existed, I just kept walking through list(dictionary.values()) which is so heavy on the CPU
19. When using while True loops, just add a time.sleep() when it's not doing anything. Even time.sleep(0.1) is enough as it lets the CPU
	chill for a bit but is fast enough to detect change
20. Now this might sound stupid but if you use a variable multiple times in a function in a class: Just store the variable locally in the function
	- for a second time. That is especially important when working with variables that you use very frequently.
	For example: I used a variable from self.config, which is a class instance inside of a class, in a loop which took up so much processing power
	as it had to keep going back to the self.config class to get the constant.
21. Work more with decorators and properties, they are much more elegant and quite simple actually
22. Another very important thing is to use all the abilities Python is giving to you. Whether it be type indicators
	- or inline function returns and such.
23. Most importantly, have a good TODO list. Having a clear TODO list with clear goals really helped me get the motivation
	- I needed to keep working on the project without feeling tired.
24. You can't iterate over a dict's values and modify the dict then.
    - Instead, do a snapshot of the dict's values and then create a new dict before deleting the old
25. JSON really doesn't like it if the key is declared using ' instead of ". Thats why integers like template or fileKey are sometimes converted 
into str.
26. If run from autorun, it sets the cwd (current working directory) as system32
27. The DBInserter is ridiculously fast but gets bottlenecked because os.walk() is quite slow
28. Instead of writing big functions to compare two classes, just check if they already have a __eq__ and __gt__ function '-'