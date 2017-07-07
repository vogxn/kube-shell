import pytest
import pexpect


class TestCLI(object):

    def test_cli_spawn(self, request, start_shell):
        self.cli = start_shell
        self.cli.expect('kube-shell> ')

    @pytest.fixture()
    def start_shell(self, request):
        cli = pexpect.spawnu('kube-shell')
        def _cleanup():
            self.cli.close()
        request.addfinalizer(_cleanup)
        return cli
