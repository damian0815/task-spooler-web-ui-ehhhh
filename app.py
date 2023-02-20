from flask import Flask, render_template, request, Response
import paramiko
import os
import time

app = Flask(__name__)


def connect() -> paramiko.SSHClient:
    server = os.environ['TSPW_SSH_SERVER']
    port = int(os.environ['TSPW_SSH_PORT'])
    username = os.environ['TSPW_SSH_USER']
    password = os.environ['TSPW_SSH_PASS']

    # Set up global SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(server, port=port, username=username, password=password)
    return ssh

ssh = connect()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/execute', methods=['POST'])
def execute():
    command = request.json['command']

    # Execute command on remote server
    print("running ", command)
    stdin, stdout, stderr = ssh.exec_command(f'ls {command}')
    stdout.channel.set_combine_stderr(True)

    # Read response from command
    response = stdout.read().decode('utf-8')

    print("response:", response)
    return render_template('index.html', response=response)


@app.route('/stream')
def stream():
    # Start the task-spooler command in the background
    stdin, stdout, stderr = ssh.exec_command('ts -t')

    print("streaming..")

    def generate():
        while not stdout.channel.exit_status_ready():
            line = stdout.readline()
            if line:
                print(f"yielding: {line}")
                yield line
            else:
                print("nothing, sleeping")
                time.sleep(0.1)

    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)