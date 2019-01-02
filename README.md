# sPycialist

![Python](https://www.python.org/static/community_logos/python-logo-master-v3-TM.png "Written in Python")

## What's this?
sPycialist is "Specialist" PC emulator written in Python. It uses my own realization of Intel 8080 CPU emulation written in Python too.

[Specialist PC on Wikipedia](https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B5%D1%86%D0%B8%D0%B0%D0%BB%D0%B8%D1%81%D1%82_(%D0%BA%D0%BE%D0%BC%D0%BF%D1%8C%D1%8E%D1%82%D0%B5%D1%80) "Specialist PC on Wikipedia")

This Intel 8080 emulator successfully passes all tests of 8080/8085 CPU Exerciser.

![8080/8085 CPU Exerciser](https://pic.maxiol.com/images/1545797292.3254906935.i8080validator2.png "8080/8085 CPU Exerciser") ![8080/8085 CPU Exerciser](https://pic.maxiol.com/images/1545797039.3254906935.i8080validator3.png "8080/8085 CPU Exerciser")

## Requirements

* Python 3
* pygame library (use 'pip install pygame' command in console for installation)

## Usage

To launch emulator use this command:

```bash
python spycialist.py
```

Press this keys sequence in the emulator for launch loaded game: F1, ENTER, U, ENTER.

To load another game put RKS file beside emulator files then change GAME constant in spycialist.py file and finally restart emulator.

## Known issues

* Low emulation speed due to general Python speed
* There is no sound emulation

## Thanks (in alphabetical order)

* ivagor
* Q-Master
* [svofski](https://github.com/svofski "svofski")
* Titus

## Screenshots

![ZOO](https://pic.maxiol.com/images/1546225871.90463878.zoo.gif "ZOO Game") ![Gold](https://pic.maxiol.com/images/1546247169.90463878.gold.gif "Gold Game")<br>
![Chess](https://pic.maxiol.com/images/1545567716.90463878.chess.png "Chess") ![Basic](https://pic.maxiol.com/images/1545798471.3254906935.chessbasic.png "Basic")

## Versions

v0.4 (2nd January, 2019)
- Code optimization
- Video optimization by svofski
- Keybord routine by ivagor

v0.3 (31st December, 2018)
- Great speed up due to screen update optimization

v0.2 (29th December, 2018)
- A lot of code optimization for speed up

v0.1 (26th December, 2018)
- Initial release
