# Copyright (c) 2020 Microsoft
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from mpi4py import MPI
from cmdstanpy import set_cmdstan_path, CmdStanModel
import os
from azureml.core import Run
from argparse import ArgumentParser
import subprocess
from datetime import datetime
import shutil

STAN_PATH = os.environ.get("STAN_PATH")

comm = MPI.COMM_WORLD

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('--data-path', '-d', type=str, help='Path to RDumps')
    parser.add_argument('--shared-model-datastore', type=str, help='Path to Shared Model Directory - shared between all nodes.')
    parser.add_argument('--nodes', '-n', type=int, help='Number of nodes test is being run on')
    parser.add_argument('--procs', '-p', type=int, help='Number of processes per node')
    parser.add_argument('--samples', '-s', type=int, help='Sample Size of RDump file')
    parser.add_argument('--stan-code-file', type=str, help="The path of the stan code file")
    args = parser.parse_args()
    return args

def generate_model_paths(model_base_directory, run, create_if_not_exists=False):
    """Create  that the model is compiled in"""
    output_path = os.path.join(model_base_directory, run.experiment.name, run.id)
    
    output_path = os.path.dirname(output_path)
    if not os.path.isdir(output_path) and create_if_not_exists:
        os.mkdir(output_path)
    
    model_path = os.path.join(output_path, "model")
    
    return {"stan_file": model_path + ".stan",
            "exe_file": model_path}
 
def compile_model(stan_file, model_path):  
    if not os.path.isfile(model_path):
        print('-- Copying Stan Code File to Shared Directory')
        shutil.copyfile(stan_file, model_path)
    
    print("-- Compiling STAN model")
    model = CmdStanModel(stan_file=model_path, compile=True)

    return model

def main(data_path, nodes, procs, samples, stan_code_file, shared_model_datastore, **kwargs):
    print("============================")
    print("========= STAN RUN =========")
    print("============================")

    start_time = datetime.now()

    print('-- Setting STAN path')
    set_cmdstan_path(STAN_PATH)

    # Elect one node as de-facto "head" node
    IS_HEAD_NODE = (comm.rank == 0)
    
    run = Run.get_context()
    # data_path = run.input_datasets['input-data']

    if IS_HEAD_NODE:
        run.log('nodes', nodes)
        run.log('nprocs', procs)
        run.log('shards', nodes*procs)
        run.log('samples', samples)

    # Compile model
    print("-- Compiling STAN model")
    model_paths = generate_model_paths(shared_model_datastore, 
                                       run=run, 
                                       create_if_not_exists=IS_HEAD_NODE)

    if IS_HEAD_NODE:
        model = compile_model(stan_code_file, model_paths['stan_file'])
    
    # Have all workers wait for the model to be compiled
    comm.Barrier()

    # If this is not the "head" node, then 
    if not IS_HEAD_NODE:   
        print('-- Loading compiled model')
        model = CmdStanModel(**model_paths, 
                             compile=False)
                              
    print('-- Running job')
    file = os.path.join(data_path, f'data_n{samples}_s{nodes*procs}.Rdump')

    comm.Barrier()
    
    # Submit MPI Run
    cmd = f'{model.exe_file} sample data file={file} output file=./outputs/output.csv'
    print(f'Calling command: "{cmd}"')
    proc_start_time = datetime.now()
    p = os.system(cmd)
     
    end_time = datetime.now()

    print(os.listdir('.'))

    print(f"Elapsed time: {end_time - start_time}")

    if IS_HEAD_NODE:
        run.log('total_time', (end_time-start_time).total_seconds())
        run.log('process_time', (end_time-proc_start_time).total_seconds())
        print('Job Finished')
        # run.complete()


if __name__ == "__main__":
    args = parse_args()
    main(**args.__dict__)