import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from skill.setup import configure
from skill.mcp_client import MCPError

class FakeClient:
    error = None
    def __init__(self, token):
        self.token = token
    def initialize(self):
        if self.error:
            raise MCPError(self.error)
    def list_tools(self):
        return [{'name':'query-meals'}]

class TestSetup(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.messages=[]
        FakeClient.error=None
    def tearDown(self):
        self.temp.cleanup()
    def run_config(self, token):
        return configure(self.root, token_reader=lambda:token, client_factory=FakeClient, output=self.messages.append)
    def test_success_saves_private_without_printing_token(self):
        self.assertTrue(self.run_config('TEST_ONLY_SECRET'))
        p=self.root/'.private/token'
        self.assertEqual(p.read_text(),'TEST_ONLY_SECRET')
        self.assertEqual(p.stat().st_mode & 0o777,0o600)
        self.assertEqual(p.parent.stat().st_mode & 0o777,0o700)
        self.assertNotIn('TEST_ONLY_SECRET','\n'.join(self.messages))
    def test_bad_token_preserves_previous(self):
        p=self.root/'.private/token';p.parent.mkdir();p.write_text('PREVIOUS_TEST_TOKEN')
        FakeClient.error='401 SECRET_MUST_NOT_BE_ECHOED'
        self.assertFalse(self.run_config('BAD_TEST_TOKEN'))
        self.assertEqual(p.read_text(),'PREVIOUS_TEST_TOKEN')
        self.assertNotIn('SECRET_MUST_NOT_BE_ECHOED','\n'.join(self.messages))
    def test_network_failure_does_not_save(self):
        FakeClient.error='无法连接官方 MCP 服务'
        self.assertFalse(self.run_config('TEST_TOKEN'))
        self.assertFalse((self.root/'.private/token').exists())
        self.assertTrue(any('不一定是 Token' in s for s in self.messages))
    def test_cancel_and_empty_do_not_save(self):
        def cancel():raise KeyboardInterrupt
        self.assertFalse(configure(self.root,token_reader=cancel,output=self.messages.append))
        self.assertFalse(self.run_config(''))
        self.assertFalse((self.root/'.private').exists())
    def test_import_launcher_does_not_prompt(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('launcher_test',Path(__file__).resolve().parents[1]/'local_setup.py')
        module=importlib.util.module_from_spec(spec)
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            spec.loader.exec_module(module)
        self.assertEqual(stream.getvalue(),'')
