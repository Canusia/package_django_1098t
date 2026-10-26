from django.test import TestCase, override_settings


class CampusTests(TestCase):
    def test_commands_are_campus_commands(self):
        from cis.management.campus_command import CampusCommand
        from django_1098t.management.commands import publish_1098t
        from django_1098t.management.commands import test_1098t_generation
        self.assertTrue(issubclass(publish_1098t.Command, CampusCommand))
        self.assertTrue(issubclass(test_1098t_generation.Command, CampusCommand))

    @override_settings(MULTI_CAMPUS=True)
    def test_filer_info_raises_without_a_campus(self):
        from cis.campus_context import NoCampusContext
        from django_1098t.constants import get_filer_info
        with self.assertRaises(NoCampusContext):
            get_filer_info()
