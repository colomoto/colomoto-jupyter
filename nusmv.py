
import os
import subprocess
import tempfile

class CmdError(subprocess.CalledProcessError):
    def __str__(self):
        stderr = "\n%s" % self.stderr.decode()
        return "Command '%s' returned non-zero exit status %d\n%s\n" \
            % (" ".join(self.cmd), self.returncode, stderr)

class NuSMVResults(dict):
    def alltrue(self):
        return False not in self.values()

class NuSMV(object):
    def __init__(self, input_smv):
        self.input_smv = input_smv
        self.__custom_specs = []
        self.opts = {
            "dcx": True,
            "coi": True,
        }

    def check_output(self):
        """
        Call NuSMV and returns the content of stdout
        """
        if self.__custom_specs:
            # we need to generate a temporary file
            fd, input_file = tempfile.mkstemp(suffix=".smv")
            with open(fd, "w") as out, open(self.input_smv) as src:
                out.write(src.read())
                for (tspec, expr, name) in self.__custom_specs:
                    out.write("{}SPEC {}{};\n".format(tspec,
                        "NAME {} := ".format(name) if name else "",
                        expr))
            todel = True
        else:
            input_file = self.input_smv
            todel = False
        args = ["NuSMV"]
        for k, v in self.opts.items():
            if isinstance(v, bool) and v:
                args.append("-%s" % k)
            else:
                raise NotImplementedError
        args.append(input_file)

        try:
            output = subprocess.check_output(args, stderr=subprocess.PIPE).decode().strip()
        except subprocess.CalledProcessError as e:
            raise CmdError(e.returncode, e.cmd, e.output, e.stderr) from None
        finally:
            if False and todel:
                os.unlink(input_file)
        return output

    def _parse_output(self, output):
        results = []
        for line in output.split("\n"):
            if not line.startswith("-- specification "):
                continue
            parts = line.split()
            valid = True if parts[-1] == "true" else False
            spec = " ".join(parts[2:-2])
            results.append((spec, valid))

        if self.__custom_specs:
            nc = len(self.__custom_specs)
            keys = [name if name else spec \
                        for (_, spec, name) in self.__custom_specs]
            results = results[:-nc] \
                + list(zip(keys, [valid for (_,valid) in results[-nc:]]))

        return NuSMVResults(results)

    def verify(self):
        output = self.check_output()
        return self._parse_output(output)

    def alltrue(self):
        return self.verify().alltrue()

    def add_spec(self, tspec, expr, *fmt, **kwargs):
        self.modified = True
        assert tspec in ["LTL", "CTL"], "Unkown specification type"
        name = kwargs.get("name")
        if fmt:
            vfmt = []
            kfmt = {}
            for v in fmt:
                if isinstance(v, dict):
                    kfmt.update(v)
                else:
                    vfmt.append(v)
            expr = expr.format(*vfmt, **kfmt)
        self.__custom_specs.append((tspec, expr, name))

    def add_ltl(self, expr, *fmt, **kwargs):
        self.add_spec("LTL", expr, *fmt, **kwargs)

    def add_ctl(self, expr, *fmt, **kwargs):
        self.add_spec("CTL", expr, *fmt, **kwargs)

    def reset(self):
        self.__custom_specs.clear()


def load(filename, may_have_specs=False):
    return NuSMV(filename)


