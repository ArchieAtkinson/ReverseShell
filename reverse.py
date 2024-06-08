import os
import pty
import select
import sys
import tty
import termios
import tempfile
from collections import deque


# ANSI escape codes for moving the cursor
ESC = '\033['

def move_cursor_up(lines=1):
    return f'{ESC}{lines}A'

def move_cursor_to_start_of_line():
    return f'{ESC}1G'


def clear_terminal():
    # ANSI escape code to clear the screen and move the cursor to the home position
    clear_screen = '\033[2J'
    move_cursor_home = '\033[H'
    
    # Combine the commands
    return clear_screen + move_cursor_home

def interactive_shell():
    # Function to spawn a new process in a pseudo-terminal
    def spawn(argv, env):
        master_fd, slave_fd = pty.openpty()

        pid = os.fork()
        if pid == 0:
            # Child process
            os.close(master_fd)
            os.setsid()
            os.dup2(slave_fd, sys.stdin.fileno())
            os.dup2(slave_fd, sys.stdout.fileno())
            os.dup2(slave_fd, sys.stderr.fileno())
            os.close(slave_fd)
            os.execvpe(argv[0], argv, env)
        else:
            # Parent process
            os.close(slave_fd)
            return master_fd, pid

    # Function to interact with the shell
    def read_shell(master_fd):
        history = b"       "
        debug_file = open("debug.txt", 'a')
        while True:
            r, _, _ = select.select([sys.stdin, master_fd], [], [])
            if sys.stdin in r:
                input_data = os.read(sys.stdin.fileno(), 1024)
                if input_data.strip() == b'exit':
                    os.write(master_fd, b'exit\n')
                    break
                os.write(master_fd, input_data)
            if master_fd in r:
                try:
                    output_data = os.read(master_fd, 1024)
                    if output_data:
                        history += output_data
                       
                        line_count = output_data.count(b'\n')
                        temp_string = b""
                        if b"\n" in output_data:
                            lines = history.split(b'\n')
                            reversed_lines = lines[::-1]
                            reversed_byte_string = b'\n'.join(reversed_lines)
                            temp_string += reversed_byte_string
                            temp_string += b'\033[H'
                            os.write(sys.stdout.fileno(), clear_terminal().encode())
                        else:
                            temp_string += output_data
                        os.write(sys.stdout.fileno(), temp_string)
                        # if line_count > 1:
                        #     temp_string += history
                        #     os.write(sys.stdout.fileno(), temp_string)
                        # else:
                        #     os.write(sys.stdout.fileno(), temp_string)
                        
                    else:
                        break
                except OSError:
                    break
        debug_file.write(history.decode('utf-8'))

    # Custom prompt
    custom_prompt = "PS1='CustomPrompt$ '"

    # Create a temporary file with the custom prompt settings
    with tempfile.NamedTemporaryFile(delete=False) as temp_rc:
        temp_rc.write(custom_prompt.encode('utf-8'))
        temp_rc_path = temp_rc.name

    # Environment variables
    env = os.environ.copy()

    # Start a bash process using a pseudo-terminal and the custom rcfile
    master_fd, pid = spawn(['bash', '--rcfile', temp_rc_path], env)

    print("Enter commands to execute in the shell. Type 'exit' to quit.")

    old_tty_attrs = termios.tcgetattr(sys.stdin)

    try:
        # Set the terminal to raw mode to handle interactive input/output
        tty.setraw(sys.stdin.fileno())
        read_shell(master_fd)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Restore the terminal to its original mode
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_tty_attrs)
        os.close(master_fd)
        # Wait for the child process to finish
        os.waitpid(pid, 0)
        # Clean up the temporary rc file
        os.remove(temp_rc_path)

# Run the interactive shell
interactive_shell()
