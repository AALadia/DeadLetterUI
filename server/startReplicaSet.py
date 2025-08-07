#!/usr/bin/env python3
"""
setup_rs.py

Automatically sets up a MongoDB replica set (rs0) in the current workspace folder.
You only need to set the MONGOD_PATH variable below to point to your mongod.exe (or its containing directory).
"""

import os
import subprocess
import time
import shutil

# ─────────────────────────────────────────────────────────────────────
# ◉ ◉ ◉  CONFIGURE THIS VARIABLE ◉ ◉ ◉
#
# Either:
#   • Full path to mongod.exe, e.g.:
#       r"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe"
#   • Or the directory containing mongod.exe, e.g.:
#       r"C:\Program Files\MongoDB\Server\8.0\bin"
#
MONGOD_PATH = r"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe"
MONGOSH_PATH = r"C:\Program Files\MongoDB\Server\8.0\bin\mongosh.exe"
# ─────────────────────────────────────────────────────────────────────


def find_executable(input_path, exe_name):
    """
    Given an input (file or directory), return the full path to exe_name.
    If input_path is a directory, append exe_name. If it's already the exe, return as is.
    Raises FileNotFoundError if not found.
    """
    input_path = os.path.abspath(input_path)
    if os.path.isdir(input_path):
        candidate = os.path.join(input_path, exe_name)
        if os.path.isfile(candidate):
            return candidate
        else:
            raise FileNotFoundError(
                f"Could not find {exe_name} in directory {input_path}")
    else:
        base = os.path.basename(input_path).lower()
        if base == exe_name.lower():
            if os.path.isfile(input_path):
                return input_path
            else:
                raise FileNotFoundError(f"File {input_path} does not exist.")
        else:
            parent = os.path.dirname(input_path)
            candidate = os.path.join(parent, exe_name)
            if os.path.isfile(candidate):
                return candidate
            else:
                raise FileNotFoundError(
                    f"Could not resolve {exe_name} from {input_path}")


def create_data_dirs(base_dir, repl_name="rs0"):
    """
    Create three subdirectories under base_dir: repl_name-1, repl_name-2, repl_name-3.
    Return a list of (dbpath, port) tuples.
    If the subdirectory exists, it will be deleted first.
    """
    ports = [27017, 27018, 27019]
    data_paths = []
    for idx, port in enumerate(ports, start=1):
        subdir = f"{repl_name}-{idx}"
        full_path = os.path.join(base_dir, subdir)
        os.makedirs(full_path, exist_ok=True)
        data_paths.append((full_path, port))
    return data_paths


def launch_mongod_instances(mongod_exe, data_paths, repl_name="rs0"):
    """
    Launch each mongod instance in a NEW console window (Windows) or background process (Unix).
    Returns a list of subprocess.Popen objects.
    """
    procs = []
    is_windows = os.name == "nt"
    for dbpath, port in data_paths:
        cmd = [
            mongod_exe, "--port",
            str(port), "--dbpath", dbpath, "--replSet", repl_name, "--bind_ip",
            "localhost"
        ]
        if is_windows:
            proc = subprocess.Popen(
                cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            stdout_log = open(os.path.join(dbpath, f"mongod-{port}.log"), "a")
            stderr_log = open(os.path.join(dbpath, f"mongod-{port}.err"), "a")
            proc = subprocess.Popen(cmd, stdout=stdout_log, stderr=stderr_log)
        procs.append(proc)
        print(f"Launched mongod (port {port}, dbpath {dbpath})")
    return procs


def initiate_replica_set(mongosh_exe, repl_name="rs0"):
    """
    Use mongo shell to run rs.initiate() with a three-member config.
    Assumes all members run on localhost:27017,27018,27019.
    """
    js_config = ("rs.initiate({ _id: '" + repl_name + "', members: ["
                 "{ _id: 0, host: 'localhost:27017' },"
                 "{ _id: 1, host: 'localhost:27018' },"
                 "{ _id: 2, host: 'localhost:27019' }"
                 "] });")
    cmd = [mongosh_exe, "--port", "27017", "--eval", js_config]
    print("Initiating replica set with configuration:")
    print(js_config)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if result.stderr.strip() != 'MongoServerError: already initialized':
            raise RuntimeError(
                f"Failed to initiate replica set: {result.stderr.strip()}")


def is_mongod_running():
    """
    Checks if any mongod.exe process is currently running on Windows.
    Returns True if found, False otherwise.
    """
    # Use tasklist with a filter for mongod.exe
    proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq mongod.exe"],
                          capture_output=True,
                          text=True)
    # The header always appears, but if no tasks match, the output will include "No tasks are running"
    if "mongod.exe" in proc.stdout:
        print("\n[!] It looks like MongoDB (mongod.exe) is already running on your computer.")
        print("    Please close all running mongod.exe processes before running this script.")
        print("    You can do this by:")
        print("      1. Pressing Ctrl + Shift + Esc to open Task Manager.")
        print("      2. Finding any 'MongoDB Database Server' processes in the list.")
        print("      3. Right-clicking each one and selecting 'End Task'.")
        print("    After closing them, run this script again.\n")
        input("Press Enter to exit...")
        exit(1)


def main():
    # Resolve mongod.exe
    try:
        mongod_exe = find_executable(MONGOD_PATH, "mongod.exe")
        mongosh_exe = find_executable(MONGOSH_PATH, "mongosh.exe")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    workspace_dir = os.getcwd()
    print(f"Workspace directory: {workspace_dir}")

    # Step 0: create a function that checks if mongod is running
    is_mongod_running()

    # Step 1: Create data directories for each member
    data_paths = create_data_dirs(workspace_dir, repl_name="rs0")

    # Step 2: Launch mongod processes
    launch_mongod_instances(mongod_exe, data_paths, repl_name="rs0")

    # Step 3: Wait for a few seconds to let mongod instances start
    print("Waiting 5 seconds for mongod instances to start...")
    time.sleep(5)

    # Step 4: Initiate the replica set
    initiate_replica_set(mongosh_exe, repl_name="rs0")
    print('____________________________________')
    print('____________________________________')
    print("Setup script completed") 
    print("- To verify open Command Prompt")
    print("- Type : cd " + os.path.dirname(mongosh_exe))
    print("- Type : mongosh")
    print("- Type : rs.status()")


if __name__ == "__main__":
    main()
