from py4j.java_gateway import JavaGateway, GatewayParameters

from subprocess import PIPE
import subprocess
import builtins

proc = None
gw = None
gs = None
lqm = None


def GINsim():
    "Launch in background a GINsim instance running the python gateway"
    close()
    
    global proc, gw, gs, lqm
    
    # Start the gateway and read the selected dynamical port
    proc = subprocess.Popen(["GINsim", "-py"], stdout=PIPE, stdin=PIPE)
    port = int(proc.stdout.readline().strip())
    
    # start the gateway and return the entry point (GINsim's ScriptLauncher)
    param = GatewayParameters(port=port, auto_convert=True, auto_field=True)
    gw = JavaGateway(gateway_parameters=param)
    
    gs = gw.entry_point
    lqm = gs.LQM()
    
    # inject gs and lqm into builtins: they will be available as global variables but preserve existing ones
    if not hasattr(builtins, 'gs'):
        builtins.gs = gs
    if not hasattr(builtins, 'lqm'):
        builtins.lqm = lqm


def close():
    "close the running GINsim if any"
    
    global proc, gw, gs,lqm
    
    if proc and gw:
        print("cleanup")
        if hasattr(builtins, 'gs') and gs == builtins.gs:
            del(builtins.gs)
        if hasattr(builtins, 'lqm') and lqm == builtins.lqm:
            del(builtins.lqm)
        
        gs = None
        lqm = None
        
        gw.shutdown()
        proc.terminate()
        proc = None
        gw = None

# Make sure to close the running instance
import atexit
atexit.register(close)


# Launch a background GINsim process
GINsim()

