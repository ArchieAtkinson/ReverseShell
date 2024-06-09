# Reverse Shell

* Toy project, not for general usage*

Modifies the terminal output grow from top to bottom. 

Standard Shell:
```bash
aa@MainPC:~/ReverseShell$ ls
README.md  logs.log  out.txt  reverse.py
aa@MainPC:~/ReverseShell$ ps
  PID TTY          TIME CMD
73717 pts/12   00:00:00 bash
74347 pts/12   00:00:00 ps
aa@MainPC:~/ReverseShell$ 
```

Reverse Shell: 
```bash
aa@MainPC:~/ReverseShell$ 
74747 pts/10   00:00:00 ps
74690 pts/10   00:00:00 bash
  PID TTY          TIME CMD
aa@MainPC:~/ReverseShell$ ps
README.md  logs.log  out.txt  reverse.py
aa@MainPC:~/ReverseShell$ ls
```

## Usage

Requires `python3`.

`python3 reverse_shell.py`

To exit the Reverse Shell, type `exit`

## Todo

- Fix issue when output is larger the terminal window
- Implement own scrolling to allow larger history 
