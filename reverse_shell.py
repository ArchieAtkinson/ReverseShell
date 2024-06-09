import os
import pty
import select
import sys
import tty
import termios
import logging

# ANSI escape codes for moving the cursor
ESC = "\033"
clear_screen = f"{ESC}[2J"
erase_saved_lines = f"{ESC}[3J"
move_cursor_home = f"{ESC}[H"

logger = logging.getLogger()


def move_cursor_up(lines=1):
    return f"{ESC}[{lines}A"


def move_cursor_to_start_of_line():
    return f"{ESC}[1G"


def clear_terminal():
    return clear_screen + move_cursor_home


def is_child_process(pid):
    return pid == 0


def read_stdin(parent_fd):
    input_data = os.read(sys.stdin.fileno(), 1024)
    logger.info(f"input_data:{input_data}")
    os.write(parent_fd, input_data)


def read_parent(parent_fd, history):
    output_data = os.read(parent_fd, 1024)
    if output_data:
        cleaned_text = output_data.replace(clear_screen.encode(), b"")
        cleaned_text = cleaned_text.replace(erase_saved_lines.encode(), b"")
        history += cleaned_text

        if b"clear\r" in history:
            history = b""

        temp_string = b""
        if b"\r" in output_data:
            lines = history.split(b"\n")
            reversed_lines = lines[::-1]
            reversed_byte_string = b"\n".join(reversed_lines)
            temp_string += reversed_byte_string
            temp_string += move_cursor_home.encode()
            os.write(sys.stdout.fileno(), clear_terminal().encode())
        else:
            temp_string += output_data

        logger.info(f"history:\n{history.decode()}")
        os.write(sys.stdout.fileno(), temp_string)
        return history
    else:
        return None


def read_shell(parent_fd):
    history = b""
    while True:
        r, _, _ = select.select([sys.stdin, parent_fd], [], [])
        if sys.stdin in r:
            read_stdin(parent_fd)
        if parent_fd in r:
            ret = read_parent(parent_fd, history)
            if ret is None:
                break
            else:
                history = ret


def spawn():
    env = os.environ.copy()
    parent_fd, child_fd = pty.openpty()

    pid = os.fork()
    if is_child_process(pid):
        logger.info(f"In Child Process")

        os.close(parent_fd)
        os.setsid()
        os.dup2(child_fd, sys.stdin.fileno())
        os.dup2(child_fd, sys.stdout.fileno())
        os.dup2(child_fd, sys.stderr.fileno())
        os.close(child_fd)
        os.execve(env["SHELL"], [env["SHELL"]], env)
        # Does not get passed here
    else:
        logger.info(f"In Parent Process")
        os.close(child_fd)
        return parent_fd, pid


def interactive_shell():
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(process)d | %(message)s"
    )
    file_handler = logging.FileHandler("logs.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info("---------- Booting! ----------")

    parent_fd, parent_pid = spawn()
    print("Now in Upper Shell")
    old_tty_attrs = termios.tcgetattr(sys.stdin)
    try:
        # Set the terminal to raw mode to handle interactive input/output
        tty.setraw(sys.stdin.fileno())
        read_shell(parent_fd)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Restore the terminal to its original mode
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty_attrs)
        os.close(parent_fd)
        # Wait for the child process to finish
        os.waitpid(parent_pid, 0)
    os.write(sys.stdout.fileno(), clear_terminal().encode())


# Run the interactive shell
interactive_shell()
