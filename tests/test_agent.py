#!/usr/bin/env python
#               OpenCenter(TM) is Copyright 2013 by Rackspace US, Inc.
##############################################################################
#
# OpenCenter is licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.  This
# version of OpenCenter includes Rackspace trademarks and logos, and in
# accordance with Section 6 of the License, the provision of commercial
# support services in conjunction with a version of OpenCenter which includes
# Rackspace trademarks and logos is prohibited.  OpenCenter source code and
# details are available at: # https://github.com/rcbops/opencenter or upon
# written request.
#
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0 and a copy, including this
# notice, is available in the LICENSE file accompanying this software.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the # specific language governing permissions and limitations
# under the License.
#
##############################################################################
#

import fixtures
import fcntl
import logging
import os
import StringIO
import sys
import testtools
import unittest

from opencenteragent import exceptions
from opencenteragent import OpenCenterAgent
from opencenteragent import utils


# Suppress WARNING logs
LOG = logging.getLogger('output')
LOG.setLevel(logging.ERROR)


class TestOpenCenterAgentWorking(unittest.TestCase):
    def setUp(self):
        self.agent = OpenCenterAgent(['-c',
                                     'tests/'
                                     'opencenter-agent-test-working.conf'],
                                     'test')
        self.output_handler = self.agent.output_handler
        self.input_handler = self.agent.input_handler
        self.result = self.agent.input_handler.fetch()
        self.result['output'] = self.output_handler.dispatch(
            self.result['input'])
        self.agent.input_handler.result(self.result)
        self.input_state = \
            self.agent.input_handler.plugins['input']['state']
        self.output_state = \
            self.agent.output_handler.plugins['output']['state']

    def tearDown(self):
        self.agent._cleanup()

    def test_input_setup(self):
        self.assertTrue(self.input_state.input_setup_called)

    def test_input_fetch(self):
        self.assertTrue(self.input_state.input_fetch_called)

    def test_input_result(self):
        self.assertEqual(self.result['input'], {'action': 'test',
                                                'id': 'test',
                                                'payload': {}})

    def test_input_teardown(self):
        # Stop it so teardown occurs
        self.agent.input_handler.stop()
        self.assertTrue(self.input_state.input_teardown_called)

    def test_output_setup(self):
        self.assertTrue(self.output_state.output_setup_called)

    def test_output_handler(self):
        self.assertTrue(self.output_state.output_handler_called)

    def test_output_result(self):
        self.assertEqual(self.result['output'], {'result_code': 0,
                                                 'result_data': None,
                                                 'result_str': 'success'})

    def test_output_teardown(self):
        # Stop it so teardown occurs
        self.agent.output_handler.stop()
        self.assertTrue(self.output_state.output_teardown_called)


class TestOpenCenterAgentInputBroken(unittest.TestCase):
    def setUp(self):
        self.agent = OpenCenterAgent(['-c',
                                     'tests/opencenter-agent-test-input'
                                     '-broken.conf'],
                                     'test')
        self.output_handler = self.agent.output_handler
        self.input_handler = self.agent.input_handler
        self.result = self.agent.input_handler.fetch()

        # TODO: Make not suck plz
        try:
            self.result['output'] = self.output_handler.dispatch(
                self.result['input'])
            self.agent.input_handler.result(self.result)
        except KeyError:
            self.key_error = True

        self.input_state = \
            self.agent.input_handler.plugins['input']['state']
        self.output_state = \
            self.agent.output_handler.plugins['output']['state']

    def tearDown(self):
        self.agent._cleanup()

    def test_input_setup(self):
        self.assertTrue(self.input_state.input_setup_called)

    def test_input_fetch(self):
        self.assertTrue(self.input_state.input_fetch_called)

    def test_input_result(self):
        self.assertEqual(self.result['input'], {'foo': 'bar'})

    def test_input_teardown(self):
        # Stop it so teardown occurs
        self.agent.input_handler.stop()
        self.assertTrue(self.input_state.input_teardown_called)

    def test_output_setup(self):
        self.assertTrue(self.output_state.output_setup_called)

    def test_output_handler(self):
        # Output plugin never dispatched
        self.assertFalse(self.output_state.output_handler_called)

    def test_output_result(self):
        # Output plugin dispatch failed
        self.assertTrue(self.key_error)

    def test_output_teardown(self):
        # Stop it so teardown occurs
        self.agent.output_handler.stop()
        self.assertTrue(self.output_state.output_teardown_called)


class TestOpenCenterAgentOutputBroken(unittest.TestCase):
    def setUp(self):
        self.agent = OpenCenterAgent(['-c',
                                     'tests/opencenter-agent-test-output-'
                                     'broken.conf'],
                                     'test')
        self.output_handler = self.agent.output_handler
        self.input_handler = self.agent.input_handler
        self.result = self.agent.input_handler.fetch()
        self.result['output'] = self.output_handler.dispatch(
            self.result['input'])
        self.agent.input_handler.result(self.result)
        self.input_state = \
            self.agent.input_handler.plugins['input']['state']
        self.output_state = \
            self.agent.output_handler.plugins['output']['state']

    def tearDown(self):
        self.agent._cleanup()

    def test_input_setup(self):
        self.assertTrue(self.input_state.input_setup_called)

    def test_input_fetch(self):
        self.assertTrue(self.input_state.input_fetch_called)

    def test_input_result(self):
        self.assertEqual(self.result['input'], {'action': 'test',
                                                'id': 'test',
                                                'payload': {}})

    def test_input_teardown(self):
        # Stop it so teardown occurs
        self.agent.input_handler.stop()
        self.assertTrue(self.input_state.input_teardown_called)

    def test_output_setup(self):
        self.assertTrue(self.output_state.output_setup_called)

    def test_output_handler(self):
        self.assertFalse(self.output_state.output_handler_called)

    def test_output_result(self):
        self.assertEqual(self.result['output'],
                         {'result_code': 253, 'result_data': '',
                          'result_str':
                          'no dispatcher found for action "test"'})

    def test_output_teardown(self):
        # Stop it so teardown occurs
        self.agent.output_handler.stop()
        self.assertTrue(self.output_state.output_teardown_called)


class OpenCenterAgentNoInitialization(OpenCenterAgent):
    """Turn off initialization to make unit testing easier."""
    def _initialize(self, argv, config_section):
        self.logger = logging.getLogger()
        self.logger.addHandler(logging.StreamHandler(sys.stderr))


class ExitCalledException(Exception):
    pass


class FakeHandler(object):
    def __init__(self, raise_exception=False):
        self.raise_exception = raise_exception
        self.stop_called = False

    def stop(self):
        self.stop_called = True
        if self.raise_exception:
            raise Exception('exception!')


class TestInfrastructure(testtools.TestCase):
    def fake_exit(self, exit_code):
        self.exit_code_set = exit_code
        raise ExitCalledException()

    def fake_fork(self):
        self.fork_called = True
        return 0

    def fake_noop(self, *args, **kwargs):
        pass

    def test_exit_no_exception(self):
        self.exit_code_set = None
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])

        def no_cleanup():
            pass
        agent._cleanup = no_cleanup

        self.assertRaises(ExitCalledException, agent._exit, None)
        self.assertEqual(self.exit_code_set, 0)

    def test_exit_exception(self):
        self.exit_code_set = None
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])

        def no_cleanup():
            pass
        agent._cleanup = no_cleanup

        class FakeExceptionForTest(Exception):
            pass

        def bar():
            raise FakeExceptionForTest('testing 123')

        try:
            bar()
        except FakeExceptionForTest:
            self.assertRaises(ExitCalledException, agent._exit, True)
        self.assertEqual(self.exit_code_set, 1)

    def test_cleanup_no_exceptions(self):
        agent = OpenCenterAgentNoInitialization([])
        agent.input_handler = FakeHandler(False)
        agent.output_handler = FakeHandler(False)
        agent._cleanup()
        self.assertTrue(agent.input_handler.stop_called)
        self.assertTrue(agent.output_handler.stop_called)

    def test_cleanup_exceptions(self):
        agent = OpenCenterAgentNoInitialization([])
        agent.input_handler = FakeHandler(True)
        agent.output_handler = FakeHandler(True)
        agent._cleanup()
        self.assertTrue(agent.input_handler.stop_called)
        self.assertTrue(agent.output_handler.stop_called)

    def test_usage(self):
        io = StringIO.StringIO()
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', io))

        agent = OpenCenterAgentNoInitialization([])
        agent._usage()

        self.assertNotEqual(io.getvalue().find('verbose'), -1)

    def test_parse_opts_bad_arg(self):
        io = StringIO.StringIO()
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', io))

        self.exit_code_set = None
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])

        try:
            agent._parse_opts(['--banana'])
        except ExitCalledException:
            pass

        self.assertEqual(self.exit_code_set, 1)
        self.assertNotEqual(io.getvalue().find('verbose'), -1)

    def test_parse_opts_sets_values(self):
        io = StringIO.StringIO()
        self.useFixture(fixtures.MonkeyPatch('sys.stdout', io))

        self.exit_code_set = None
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])
        background, debug, config_file = agent._parse_opts(
            ['--config', 'gerkin', '--verbose', '-d'])

        self.assertEqual(self.exit_code_set, None)
        self.assertEqual(len(io.getvalue()), 0)

        self.assertTrue(background)
        self.assertTrue(debug)
        self.assertEqual(config_file, 'gerkin')

    def test_configure_logs_no_config(self):
        agent = OpenCenterAgentNoInitialization([])
        agent._configure_logs(None)

    def test_configure_logs_bogus_config(self):
        agent = OpenCenterAgentNoInitialization([])

        # If we pass a bogus config we should end up with the same handlers
        # at the end as we did beforehand.
        handlers_before = len(agent.logger.handlers)
        agent._configure_logs('this is a bogus config')
        self.assertEquals(len(agent.logger.handlers), handlers_before)

    def test_read_config_missing(self):
        agent = OpenCenterAgentNoInitialization([])
        agent.config_section = 'taskerator'
        with utils.temporary_file() as config_file:
            os.remove(config_file)
            self.assertRaises(exceptions.FileNotFound, agent._read_config,
                              config_file)

    def test_read_config_empty(self):
        agent = OpenCenterAgentNoInitialization([])
        agent.config_section = 'taskerator'
        with utils.temporary_file() as config_file:
            self.assertRaises(exceptions.NoConfigFound, agent._read_config,
                              config_file)

    def test_read_config_simple_with_default(self):
        agent = OpenCenterAgentNoInitialization([])
        with utils.temporary_file() as config_file:
            with open(config_file, 'w') as f:
                f.write("""[taskerator]
endpoint = http://127.0.0.1:8080/admin
banana = False""")

            agent.config_section = 'taskerator'
            config = agent._read_config(
                config_file, defaults={'taskerator': {'banana': True}})
            self.assertTrue(config['taskerator']['banana'])
            self.assertEqual(config['taskerator']['endpoint'],
                             'http://127.0.0.1:8080/admin')

    def test_read_config_with_included_file(self):
        agent = OpenCenterAgentNoInitialization([])
        with utils.temporary_directory() as path:
            config_file = os.path.join(path, 'config')
            included_file = os.path.join(path, 'included')

            with open(config_file, 'w') as f:
                f.write("""[taskerator]
endpoint = http://127.0.0.1:8080/admin
include = %s""" % included_file)

            agent.config_section = 'taskerator'
            self.assertRaises(RuntimeError, agent._read_config, config_file)

            with open(included_file, 'w') as f:
                f.write("""[taskerator]
included_value = fish""")

            config = agent._read_config(config_file)
            self.assertEquals(config['taskerator']['endpoint'],
                              'http://127.0.0.1:8080/admin')
            self.assertEqual(config['taskerator']['included_value'], 'fish')

    def test_read_config_with_included_directory(self):
        agent = OpenCenterAgentNoInitialization([])
        with utils.temporary_directory() as path:
            config_file = os.path.join(path, 'config')
            included_dir = os.path.join(path, 'included')

            with open(config_file, 'w') as f:
                f.write("""[taskerator]
endpoint = http://127.0.0.1:8080/admin
original = foo
include_dir = %s""" % included_dir)

            agent.config_section = 'taskerator'
            self.assertRaises(RuntimeError, agent._read_config, config_file)

            os.mkdir(included_dir)
            with open(os.path.join(included_dir, 'banana'), 'w') as f:
                f.write("""[taskerator]
endpoint = notthis""")

            config = agent._read_config(config_file)
            self.assertEquals(config['taskerator']['endpoint'],
                              'http://127.0.0.1:8080/admin')

            with open(os.path.join(included_dir, 'foo.conf'), 'w') as f:
                f.write("""[taskerator]
endpoint = butthis""")

            config = agent._read_config(config_file)
            self.assertEquals(config['taskerator']['endpoint'], 'butthis')
            self.assertEquals(config['taskerator']['original'], 'foo')

    def test_handle_pidfile_exists(self):
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        with utils.temporary_file() as pid_file:
            with open(pid_file, 'a+') as pidfile:
                fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                agent = OpenCenterAgentNoInitialization([])
                agent.config_section = 'testing'
                agent.config = {'testing': {'pidfile': pid_file}}

                self.assertRaises(ExitCalledException, agent._handle_pidfile)

    def test_handle_pidfile_new(self):
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        with utils.temporary_file() as pid_file:
            agent = OpenCenterAgentNoInitialization([])
            agent.config_section = 'testing'
            agent.config = {'testing': {'pidfile': pid_file}}
            agent._handle_pidfile()

            with open(pid_file, 'r') as pidfile:
                pid_from_pidfile = int(pidfile.read())
            self.assertEqual(os.getpid(), pid_from_pidfile)

    def test_setup_scaffolding_simple(self):
        def fake_parse_opts(self):
            return False, False, None

        self.fork_called = False
        self.useFixture(fixtures.MonkeyPatch('os.fork', self.fake_fork))
        self.useFixture(fixtures.MonkeyPatch('os.setsid', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('os.chdir', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])
        agent._parse_opts = fake_parse_opts
        agent._setup_scaffolding([])
        self.assertNotEqual(agent.logger.getEffectiveLevel(), logging.DEBUG)
        self.assertFalse(self.fork_called)

    def test_setup_scaffolding_debug(self):
        def fake_parse_opts(self):
            return False, True, None

        self.fork_called = False
        self.useFixture(fixtures.MonkeyPatch('os.fork', self.fake_fork))
        self.useFixture(fixtures.MonkeyPatch('os.setsid', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('os.chdir', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])
        agent._parse_opts = fake_parse_opts
        agent._setup_scaffolding([])

        print type(agent.logger)
        self.assertEqual(agent.logger.getEffectiveLevel(), logging.DEBUG)
        self.assertFalse(self.fork_called)

    def test_setup_scaffolding_daemonize(self):
        def fake_parse_opts(self):
            return True, False, None

        self.fork_called = False
        self.useFixture(fixtures.MonkeyPatch('os.fork', self.fake_fork))
        self.useFixture(fixtures.MonkeyPatch('os.setsid', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('os.chdir', self.fake_noop))
        self.useFixture(fixtures.MonkeyPatch('sys.exit', self.fake_exit))

        agent = OpenCenterAgentNoInitialization([])
        agent._parse_opts = fake_parse_opts
        agent._setup_scaffolding([])

        print type(agent.logger)
        self.assertNotEqual(agent.logger.getEffectiveLevel(), logging.DEBUG)
        self.assertTrue(self.fork_called)


if __name__ == '__main__':
    unittest.main()
