import os
import random
import re
import select
import socket
import subprocess
import tempfile

from typing import Iterable, List

from aistats.oracle.oracle_caller import OracleCaller
from clauses.cnf import Predicate, WeightedFormula


class ForcliftV1(OracleCaller):

    OUTPUT_PATTERN = re.compile(r"Z\s*=\s*exp\((.*?)\)")

    def __init__(self, path):
        super().__init__()
        self.path = path

    def call_oracle(self, domain_size: int, atoms: Iterable[Predicate], cnfs: List[WeightedFormula],) -> float:
        with tempfile.TemporaryDirectory() as td:
            tmp_file = os.path.join(td, "input.mln")
            self.write_file(domain_size, atoms, cnfs, tmp_file)
            try:
                f_out = subprocess.check_output(["java", "-jar", self.path, "-z", tmp_file])
            except subprocess.CalledProcessError as e:
                raise ValueError("WFOMC call failed.")
        s_out = str(f_out, encoding='utf-8')
        f_z_match = re.search(self.OUTPUT_PATTERN, s_out)
        if f_z_match is None:
            raise ValueError("Cannot find partition function value in WFOMC output.")
        return float(f_z_match.group(1))

    def write_file(self, domain_size: int, atoms: Iterable[Predicate], cnfs: List[WeightedFormula], f_name: str):
        domain_name = "dom"
        domain = f"{domain_name} = {{ 1, ..., {domain_size} }}\n"
        with open(f_name, "w") as file:
            file.write(domain)
            file.writelines(f"{p.with_domain(domain_name)}\n" for p in atoms)
            file.writelines(f"{cnf.weight} {cnf.formula}\n" for cnf in cnfs)


class ForcliftClientCaller(ForcliftV1):

    def __init__(self, wrapper_path: str = None, port: int = -1, sockets: int = 1, start_new: bool = False):
        super().__init__()
        if start_new and wrapper_path is None:
            raise ValueError("Must specify path to Forclift wrapper if start_new=True")
        if not start_new and not 0 < port < 2**16:
            raise ValueError(f"Invalid port number {port} for start_new=False")
        self.port = port if port > 0 else random.randint(7300, 7400)
        self.server = self.start_server(wrapper_path) if start_new else None
        self.sockets = self._prepare_sockets(sockets)

    def __del__(self):
        self.shutdown()

    def start_server(self, path):
        print(f"Starting the server on port {self.port}")
        return subprocess.Popen(["java", "-jar", path, str(self.port)], stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)

    def _prepare_sockets(self, sockets: int):
        sock_list = []
        for i in range(sockets):
            n_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                n_sock.connect(("127.0.0.1", self.port))
            except ConnectionRefusedError as e:
                print(e)
                print("Connection refused... wait a moment and try once again")
                import time
                time.sleep(5)
                n_sock.connect(("127.0.0.1", self.port))
            n_sock.setblocking(False)
            sock_list.append(n_sock)
        return sock_list

    def call_oracle(self, domain_size: int, atoms: Iterable[Predicate], cnfs: List[WeightedFormula]) -> float:
        with tempfile.TemporaryDirectory() as td:
            tmp_file = os.path.join(td, "input.mln")
            self.write_file(domain_size, atoms, cnfs, tmp_file)
            z_value = self.send_input(tmp_file)
        return z_value

    def send_input(self, file_name) -> float:
        rcvb = []
        r, w, e = select.select(self.sockets, self.sockets, [], 5)
        use_sock = w[0]
        use_sock.send(bytes(f"{file_name}\n", encoding='utf-8'))
        while True:
            r, w, e = select.select([use_sock], [use_sock], [], 5)
            if len(r) > 0:
                data = r[0].recv(1024)
                if not data:
                    print("Server probably shut down")
                    raise Exception("Server shut down...")
                else:
                    rcvb.append(data)
                    if data.endswith(b"\n"):
                        out = b"".join(rcvb)
                        rcvb = []
                        if out in [b"ERR\n", b"CALC_ERR\n", b"CLOSE\n"]:
                            raise ValueError("Calculation error")
                        return float(out)

    def send_shutdown(self):
        no_break = True
        shut_down = False
        rcvb = []
        while no_break:
            read, write, err = select.select(self.sockets, self.sockets, [], 5)
            if shut_down:
                no_break = False
            elif len(write) > 0:
                sock = write[0]
                sock.send(b"SHUTDOWN\n")
                shut_down = True
            for sock in read:
                data = sock.recv(1024)
                if not data:
                    print("Server disconnected")
                    no_break = True
                else:
                    rcvb.append(data)
                    if data.endswith(b"\n"):
                        out = b"".join(rcvb)
                        print(out)
                        rcvb = []
                        if out == b"SHUTTING_DOWN\n":
                            no_break = False

    def shutdown(self):
        if self.server is not None:
            try:
                self.send_shutdown()
            except Exception as e:
                print(e)
                print("Kill forclift-wrapper process")
                import os
                import signal
                os.kill(self.server.pid, signal.SIGKILL)
        for sock in self.sockets:
            sock.close()
