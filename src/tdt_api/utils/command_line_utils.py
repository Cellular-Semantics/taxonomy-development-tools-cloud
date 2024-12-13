import subprocess
import logging


def runcmd(cmd, supress_exceptions=False, cwd=None, supress_logs=False):
    """
    Runs the given command in the command line.
    :param cmd: command to run
    :param supress_exceptions: flag to suppress the exception on failure
    :param supress_logs: flag to suppress the logs in the output
    :return: output of the command
    """
    log_info("RUNNING: {}".format(cmd), supress_logs)
    p = subprocess.Popen([cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd, shell=True, universal_newlines=True)
    (out, err) = p.communicate()
    log_info('OUT: {}'.format(out), supress_logs)
    if err:
        log_error("Error: " + err, supress_logs)
    if not supress_exceptions and p.returncode != 0:
        raise Exception('Failed: {}: {}'.format(cmd, err))
    return out


def log_info(msg, supress_logs=False):
    """
    Logs the given message as info.
    :param msg: message to log
    :param supress_logs: flag to suppress the logs in the output
    """
    if not supress_logs:
        logging.info(msg)


def log_error(msg, supress_logs=False):
    """
    Logs the given message as error.
    :param msg: error message to log
    :param supress_logs: flag to suppress the logs in the output
    """
    if not supress_logs:
        logging.error(msg)