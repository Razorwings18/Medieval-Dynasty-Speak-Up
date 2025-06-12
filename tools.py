def Log(text):
    """
    Outputs text to a log file ("log.txt") in the root directory. Creates it first if it doesn't exit.
    """
    with open("log.txt", "a") as f:
        f.write(text + "\n")

def ClearLog():
    """
    Clears the log file ("log.txt") in the root directory.
    """
    with open("log.txt", "w") as f:
        f.write("")