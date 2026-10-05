"""Small unit contract for the native restore's QA04 ownership gate."""
import unittest
from pathlib import Path

from container_guard import validate_owned_container


class ContainerGuardTests(unittest.TestCase):
    def test_accepts_only_matching_socket_nonce_and_isolated_mounts(self):
        socket = Path('/root/kidsmap-task33/.tmp/kidsmap-task33-qa04-socket-abc/socket')
        info = {
            'Config': {'Labels': {'kidsmap.task33.owner': 'known-nonce'}},
            'HostConfig': {'NetworkMode': 'none', 'PortBindings': {},
                           'Tmpfs': {'/var/lib/postgresql/data': 'rw'}},
            'Mounts': [{'Type': 'bind', 'Source': str(socket), 'Destination': '/qa-socket'}],
        }
        validate_owned_container(info, nonce='known-nonce', socket=socket)
        for changed in (
            {'Config': {'Labels': {'kidsmap.task33.owner': 'wrong'}}},
            {'HostConfig': {'NetworkMode': 'bridge'}},
            {'HostConfig': {'PortBindings': {'5432/tcp': [{'HostPort': '5432'}]}}},
            {'HostConfig': {'Tmpfs': {}}},
            {'Mounts': [{'Type': 'bind', 'Source': '/tmp/other', 'Destination': '/qa-socket'}]},
        ):
            broken = {**info, **{key: {**info[key], **value} if isinstance(value, dict) and key != 'Mounts' else value
                                for key, value in changed.items()}}
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                validate_owned_container(broken, nonce='known-nonce', socket=socket)


if __name__ == '__main__':
    unittest.main()
