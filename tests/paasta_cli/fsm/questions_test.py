import mock
import testify as T

import fsm
from service_wizard.questions import get_clusternames_from_deploy_stanza


class QuestionsTestCase(T.TestCase):
    @T.setup_teardown
    def setup_mocks(self):
        """Calling raw_input() from automated tests can ruin your day, so we'll
        mock it out even for those situations where we don't care about it and
        "shouldn't" call raw_input().
        """
        with mock.patch("service_wizard.questions.ask", autospec=True) as (
            self.mock_ask
        ):
            yield


class GetSrvnameTestCase(QuestionsTestCase):
    def test_arg_passed_in(self):
        """If a value is specified, use it."""
        srvname = "services/fake"
        auto = "UNUSED"
        expected = srvname
        actual = fsm.get_srvname(srvname, auto)
        T.assert_equal(expected, actual)
        T.assert_equal(0, self.mock_ask.call_count)

    def test_arg_not_passed_in_auto_true(self):
        """If a value is not specified but --auto was requested, calculate and
        use a sane default.

        In this specific case there is no sane default, so blow up.
        """
        srvname = None
        auto = True
        T.assert_raises_and_contains(
            SystemExit,
            "I'd Really Rather You Didn't Use --auto Without --service-name",
            fsm.get_srvname,
            srvname,
            auto,
        )
        T.assert_equal(0, self.mock_ask.call_count)

    def test_arg_not_passed_in_auto_false(self):
        """If a value is not specified but and --auto was not requested, prompt
        the user.
        """
        srvname = None
        auto = False
        fsm.get_srvname(srvname, auto)
        T.assert_equal(1, self.mock_ask.call_count)


class GetSmartstackStanzaTestCase(QuestionsTestCase):
    @T.setup
    def setup_canned_data(self):
        self.yelpsoa_config_root = "fake_yelpsoa_config_root"
        self.suggested_port = 12345
        self.expected_stanza = {
            "main": {
                "proxy_port": self.suggested_port,
            }
        }

    def test_arg_passed_in(self):
        """If a port is specified, use it."""
        port = self.suggested_port
        auto = "UNUSED"

        actual = fsm.get_smartstack_stanza(self.yelpsoa_config_root, auto, port)

        T.assert_equal(self.expected_stanza, actual)
        T.assert_equal(0, self.mock_ask.call_count)

    def test_arg_not_passed_in_auto_true(self):
        """If a value is not specified but --auto was requested, calculate and
        use a sane default.
        """
        yelpsoa_config_root = "fake_yelpsoa_config_root"
        port = None
        auto = True

        with mock.patch(
            "service_wizard.questions.suggest_smartstack_proxy_port",
            autospec=True,
            return_value=self.suggested_port,
        ) as (
            self.mock_suggest_smartstack_proxy_port
        ):
            actual = fsm.get_smartstack_stanza(yelpsoa_config_root, auto, port)

        self.mock_suggest_smartstack_proxy_port.assert_called_once_with(
            yelpsoa_config_root)
        T.assert_equal(self.expected_stanza, actual)
        T.assert_equal(0, self.mock_ask.call_count)

    def test_arg_not_passed_in_auto_false(self):
        """If a value is not specified and --auto was not requested, prompt
        the user.
        """
        yelpsoa_config_root = "fake_yelpsoa_config_root"
        port = None
        suggested_port = 12345
        auto = False

        self.mock_ask.return_value = suggested_port
        with mock.patch(
            "service_wizard.questions.suggest_smartstack_proxy_port",
            autospec=True,
            return_value=suggested_port,
        ) as (
            self.mock_suggest_smartstack_proxy_port
        ):
            actual = fsm.get_smartstack_stanza(yelpsoa_config_root, auto, port)

        self.mock_suggest_smartstack_proxy_port.assert_called_once_with(
            yelpsoa_config_root)
        T.assert_equal(self.expected_stanza, actual)
        self.mock_ask.assert_called_once_with(
            mock.ANY,
            suggested_port,
        )


class GetMonitoringStanzaTestCase(QuestionsTestCase):
    def test_arg_passed_in(self):
        team = "america world police"
        auto = "UNUSED"

        actual = fsm.get_monitoring_stanza(auto, team)
        T.assert_in(("team", team), actual.items())
        T.assert_in(("service_type", "marathon"), actual.items())

    def test_arg_not_passed_in_auto_true(self):
        """If a value is not specified but --auto was requested, calculate and
        use a sane default.
        """
        team = None
        auto = True

        T.assert_raises_and_contains(
            SystemExit,
            "I'd Really Rather You Didn't Use --auto Without --team",
            fsm.get_monitoring_stanza,
            auto,
            team,
        )
        T.assert_equal(0, self.mock_ask.call_count)

    def test_arg_not_passed_in_auto_false(self):
        """If a value is not specified but --auto was not requested, prompt the
        user.
        """
        team = None
        auto = False

        actual = fsm.get_monitoring_stanza(auto, team)
        T.assert_equal(1, self.mock_ask.call_count)
        T.assert_in(("team", self.mock_ask.return_value), actual.items())

    def test_arg_not_passed_in_auto_true_legacy_style_true(self):
        """If a value is not specified and --auto was requested and
        legacy_style is on, prompt the user.
        """
        team = None
        auto = True

        actual = fsm.get_monitoring_stanza(auto, team, legacy_style=True)
        T.assert_equal(1, self.mock_ask.call_count)
        T.assert_in(("team", self.mock_ask.return_value), actual.items())

    def test_service_type_marathon_when_legacy_style_true(self):
        team = "whatever"
        auto = "UNUSED"

        actual = fsm.get_monitoring_stanza(auto, team, legacy_style=True)
        T.assert_in(("service_type", "classic"), actual.items())


class GetDeployStanzaTestCase(QuestionsTestCase):
    def test(self):
        actual = fsm.get_deploy_stanza()
        T.assert_in("pipeline", actual.keys())
        actual["pipeline"] = actual["pipeline"]

        for expected_entry in (
            {"instancename": "itest"},
            {"instancename": "security-check"},
            {"instancename": "performance-check"},
            {"instancename": "pnw-stagea.main"},
            {
                "instancename": "nova-prod.canary",
                "trigger_next_step_manually": True,
            },
        ):
            T.assert_in(expected_entry, actual["pipeline"])


class GetClusternamesFromDeployStanzaTestCase(QuestionsTestCase):
    def test_empty(self):
        deploy_stanza = {}
        expected = set()
        actual = get_clusternames_from_deploy_stanza(deploy_stanza)
        T.assert_equal(expected, actual)

    def test_non_empty(self):
        deploy_stanza = {}
        deploy_stanza["pipeline"] = [
            {"instancename": "itest", },
            {"instancename": "push-to-registry", },
            {"instancename": "mesosstage.canary", },
            {"instancename": "norcal-devc.main", "trigger_next_step_manually": True, },
            {"instancename": "nova-prod.main.with.extra.dots", },
            {"instancename": "clustername-without-namespace", },
        ]
        expected = set([
            "mesosstage",
            "norcal-devc",
            "nova-prod",
            "clustername-without-namespace",
        ])
        actual = get_clusternames_from_deploy_stanza(deploy_stanza)
        T.assert_equal(expected, actual)


class GetMarathonStanzaTestCase(QuestionsTestCase):
    def test(self):
        actual = fsm.get_marathon_stanza()
        T.assert_in("main", actual.keys())
        T.assert_in("canary", actual.keys())
