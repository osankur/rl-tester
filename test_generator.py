import argparse
import subprocess
import logging
import os
import sys
import shutil
import aiger
from functools import reduce

make_aag_script = "./scripts/make-aag.sh"
strip_output_script = "./scripts/strip_outputs"

class ANSI:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    RESET = "\033[0m"


def synthesize(reqs, output_dir):
    """
    Given set of requirement files (in Verilog), for each file req, and each output o that contains 'objective' in its name,
    compute the product of all requirements and make the objective /\_e ~e /\ o, where e ranges over all outputs of all files
    that contain 'error' in their names. Compute a best-effort strategy for each of these objectives.
    Furthermore, for each errr output e, we also compute strategies for objective /\_{e' != e} ~e' /\ e,
    thus seeing e as n an objective.
    """
    tmp_folder="/tmp/"
    product_file = f"{tmp_folder}all_reqs.aag"
    tmp_strat_file=f"{tmp_folder}strat.aag"
    base_names=dict({ (r,os.path.splitext(os.path.basename(r))[0].replace(".","_")) for r in reqs})

    if (len(set(base_names.values())) < len(reqs)):
        logging.fatal(f"Base names of requirement files must be disjoint")
        sys.exit(-1)

    # Copy every req file to tmp and convert to aag
    for req in reqs:
        tmpfile = tmp_folder + base_names[req]
        print(f"tmp file: {tmpfile}")
        shutil.copyfile(req, tmpfile)
        comp_proc = subprocess.run([make_aag_script, tmpfile],capture_output=True)
        if (comp_proc.returncode != 0):
            logging.fatal(f"Failed to convert {req} to aag")
            print(comp_proc.stderr)
            sys.exit(-1)

    # Relabel latches by adding the base filename as a prefix
    aag_files=dict()
    for req in reqs:
        aag_filename = tmp_folder + base_names[req] + ".aag"
        try:
            aag_files[req] = aiger.load(aag_filename)
        except ValueError as e:
            if "Failed to parse aag/aig HEADER" in str(e):
                comp_proc = subprocess.run(["aigmove", aag_filename, aag_filename],capture_output=True)
                if (comp_proc.returncode != 0):
                    logging.fatal(f"Failed to apply aigmove to aag {aag_filename}")
                    print(comp_proc.stderr)
                    sys.exit(-1)
                aag_files[req] = aiger.load(aag_filename)
            else:
                raise e
    renamed_aag = dict()
    for (req,aag) in aag_files.items():
        subst = dict([(l, base_names[req] + "_" + l) for l in list(aag.latches)])
        renamed_aag[req] = aag.relabel("latch", subst)
        subst = dict([(l, base_names[req] + "_" + l) for l in list(aag.outputs)])
        renamed_aag[req] = renamed_aag[req].relabel("output", subst)
        #print(renamed_aag[req])

    errors = set([])
    objectives = set([])
    for (req,aag) in renamed_aag.items():
        for out in aag.outputs:
            if "error" in out:
                errors.add(out)
            if "objective" in out:
                objectives.add(out)

    logging.info(f"Found following error monitors: {errors}")
    logging.info(f"Found following test objectives: {objectives}")
    
    # For each objectiven or error, compute product and compute new objective
    logging.debug(f"Product written to {product_file}")
    for obj in objectives:
    #for obj in objectives | errors:
        logging.info(f"Synthesizing strategy for {obj}...")
        # Product of all circuits
        product = reduce(lambda x,y: x | y, renamed_aag.values())
        # New objective is obj /\ /\_e ~e (for all errors e, e != obj)
        newobj = reduce(lambda x,y: x & y, map(lambda x: ~product.node_map[x], errors - set([obj])), product.node_map[obj])
        newoutputs = product.node_map.discard(obj) + {obj : newobj}
        aiger.AIG(inputs = product.inputs, node_map = newoutputs, latch_map= product.latch_map, latch2init=product.latch2init, comments = product.comments)
        product.write(product_file) 
        strat_file = os.path.join(f"{output_dir}",f"teststrategy_{obj}.aag")
        comp_proc = subprocess.run(["abssynthe", "-b", "-x", obj, product_file, "-o", tmp_strat_file],capture_output=True)
        if (comp_proc.returncode == 20):
            logging.info(f"{ANSI.GREEN}Successful.{ANSI.RESET} Test strategy written to {strat_file}")
        elif (comp_proc.returncode == 10):
            logging.info(f"{ANSI.RED}Failed: objective unreachable{ANSI.RESET}")
        else:
            logging.error(f"{ANSI.RED}{ANSI.BOLD}{ANSI.NEGATIVE}Abssynthe failed with code {comp_proc.returncode} on objective {obj}{ANSI.RESET}")
            print(comp_proc.stdout)
            print(comp_proc.stderr)
        subprocess.run([strip_output_script, obj, tmp_strat_file, strat_file],capture_output=True, check=True)

def main():
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser(description="Test Generator")
    parser.add_argument('-r','--requirements', nargs='+', dest='reqs', help='Set of requirements in Verilog', required=True)
    parser.add_argument("-o", "--output", type=str, dest="output",
                        help="Output directory in which the test strategies will be written",required=True)

    args = parser.parse_args()
    for file in args.reqs:
        if not os.path.exists(file):
            logging.fatal(f"File {file} not found")
            sys.exit(-1)
        if not file.endswith(".v"):
            logging.fatal(f"All requirements must be Verilog files with extension .v: {file}")
            sys.exit(-1)
    if not os.path.exists(args.output) or not os.path.isdir(args.output):
        logging.fatal(f"{args.output} is not a directory")
        sys.exit(-1)

    for exec in ["yosys", "berkeley-abc", "abssynthe","aigtoaig"]:
        if (shutil.which(exec) is None):
            logging.fatal(f"Could not find {exec} in path")
            sys.exit(-1)
    if not os.path.exists(make_aag_script):
        logging.fatal(f"{make_aag_script} not found")
        sys.exit(-1)
    if not os.path.exists(strip_output_script):
        logging.fatal(f"{strip_output_script} not found")
        sys.exit(-1)
    synthesize(args.reqs, args.output)
main()


