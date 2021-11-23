This is a tool for working with the song file format for [Shake Tracker](https://sourceforge.net/projects/cheesetronic/files/Shake%20Tracker/) by [Juan Linietsky](https://github.com/reduz).

It can do two things:

1. Convert Shake Tracker 0.2.x song files to 0.4.x.
2. Load and show the internal details of a 0.4.x song file.

---

I wrote this because I had a number of song files I made in Shake Tracker 0.2.x (or maybe it's 0.3.x, I'm not sure), but I couldn't find a copy of it anywhere. Using hints from the 0.1.x and 0.4.x source code, and the song files that I had, I reverse-engineered the format and created this tool to convert them to 0.4.x so I could load them in Shake Tracker 0.4.x.

The conversion is imperfect/incomplete, because I only needed it to work with the files that I had, and I didn't have any other files available to test with. I know for sure these things aren't working:

1. Midi bank & device settings
2. Custom/initial controller values

They're filled in with new-song defaults so that converted song files will load and still work, although you may need to fix the midi device settings after loading. I never customized any of those values so everything worked fine, but I did have to select the correct output device on the user device tab.
