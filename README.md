# uOttawa Gym Scheulder

This project automatically reserves a spot at the uOttawa gyms given a set of days and times you would like to go to the gym.  

It is built as a modified version of photonized's scheduler which you can check out [here](https://github.com/photonized/uOttawa-Gym-Scheduler).  

This is a completely hands-free program and once you have it setup, you'll never have to modify the code or rerun the docker container.  You can also set it to run for multiple users.

## Usage

1. Edit the gym.txt file with your preferred dates and times.  The format is as follows:
```
[Name]
[Barcode]
[Pin]
[Day] [Time]*
```
You can insert as many Days/Times as you'd like on each new line.  
To end a user entry, simply make sure there is an empty line after all of your day/time inputs.
Make sure there is an empty line after the last entry, so just press enter twice after your last entry.

An example of the proper format is shown in gym.txt.

2. With docker installed, build the docker container using: ```docker build uottawa-gym-scheduler .```
3. Next run the container with: ```docker run --name uottawa-gym-scheduler uottawa-gym-scheduler```
4. All done! Now you have a fully automated gym scheduler so you never have to worry about booking.
