import logging
import subprocess
logging.basicConfig(level = logging.INFO)


""" Determine if therer's a current job running. """
with open("jobstatus") as jobstatus_file:
    if jobstatus_file.read() == "active":
        logging.info("An active job exists, quitting...")
        quit(0)
logging.info("No job active rolling a restart process...")


""" Runs shell commands. """
def run_shell_command(command: str) -> str:
    process = subprocess.run(command, shell = True, capture_output = True, text = True)     
    return process.stdout


""" Determine the docker containers that are running. """   
docker_containers = run_shell_command("docker ps -q")
if docker_containers != "":
    """Stop any running docker containers"""
    logging.info(f"Stopping container(s): {docker_containers}")
    logging.info(run_shell_command(f"docker stop {docker_containers}"))


""" Start a new docker container """
logging.info(run_shell_command("docker build . - chrome-with-extensions:latest"))
logging.info(run_shell_command("docker run --restart unless-stopped -p 4444:4444 -d chrome-with-extensions:latest"))