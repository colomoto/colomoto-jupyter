
import os
import subprocess
import tempfile

import colomoto.setup_helper

class CmdError(subprocess.CalledProcessError):
    def __str__(self):
        stderr = "\n%s" % self.stderr.decode()
        return "Command '%s' returned non-zero exit status %d\n%s\n" \
            % (" ".join(self.cmd), self.returncode, stderr)

def check_output(args, timeout=None, **opts):
    try:
        return subprocess.check_output(args, stderr=subprocess.PIPE,
                    timeout=timeout, **opts).decode().strip()
    except subprocess.CalledProcessError as e:
        raise CmdError(e.returncode, e.cmd, e.output, e.stderr) from None

class NuSMVResults(dict):
    def alltrue(self):
        return False not in self.values()

class ITSModel(object):
    def __init__(self, model_file, file_type="ROMEO"):
        self.model_file = model_file
        self.file_type = file_type

    def reachability(self, state_formula, timeout=None):
        """
        Check for the reachability a state verifying the given state formula.

        :param str state_formula: State formula
        :returns: `True` if the specified state is reachable from the model initial
            state, `False` otherwise.
        :keyword int timeout: timeout in seconds
        """
        args = ["its-reach", "-i", self.model_file, "-t", self.file_type,
                "-reachable", state_formula,
                "--quiet", "--nowitness"]
        output = check_output(args, timeout=timeout)
        for line in output.split("\n"):
            if line.startswith("Reachability property "):
                res = line.strip().split()
                return res[-1] == "true."
        raise ValueError("Cannot parse output of its-reach ({})".format(output))

    def count_reachable(self, timeout=None, raw_args=[]):
        """
        :keyword int timeout: timeout in seconds
        :returns: the number of reachable states
        """
        args = ["its-reach", "-i", self.model_file, "-t", self.file_type,
                "--fixpass", "0", "--quiet"] + raw_args
        output = check_output(args, timeout=timeout)
        for line in output.split("\n"):
            if line.startswith(" Total reachable state count : "):
                res = line.split(" ")
                return int(res[-1])
        raise ValueError("Cannot parse output of its-reach ({})".format(output))

    def verify_ctls(self, specs, timeout=None, raw_args=[]):
        if isinstance(specs, dict):
            keys = []
            ctls = []
            for k, ctl in specs.items():
                keys.append(k)
                ctls.append(ctl)
        else:
            keys = None
            ctls = specs

        fd, ctl_file = tempfile.mkstemp(suffix=".ctl")
        with open(fd, "w") as out:
            for ctl in ctls:
                out.write("{};\n".format(ctl))
        args = ["its-ctl", "-i", self.model_file, "-t", self.file_type,
                    "-ctl", ctl_file, "--quiet"] + raw_args
        try:
            output = check_output(args, timeout=timeout)
        finally:
            os.unlink(ctl_file)

        res = []
        for line in output.split("\n"):
            if line.startswith("Formula is "):
                parts = line.split()
                res.append(parts[2] == "TRUE")
        if keys:
            return dict(zip(keys, res))
        return res

    def verify_ctl(self, ctl_expr, **opts):
        return self.verify_ctls([ctl_expr], **opts)[0]


