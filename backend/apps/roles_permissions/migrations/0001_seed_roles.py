from django.db import migrations

# CMS_BUILD_PROMPT.md §5.4's illustrative matrix. Roles are just permission bundles —
# nothing hardcoded in application code, this migration only seeds a sensible starting
# point that's fully editable afterward through the Role API.
EDITOR_EXCLUDED_CODENAMES = {
    "manage_users",
    "manage_settings",
    "add_user",
    "change_user",
    "delete_user",
    "add_group",
    "change_group",
    "delete_group",
}


def seed_roles(apps, schema_editor):
    # Permission rows are normally created by the post_migrate signal, which only
    # fires once at the very end of a `migrate` run — not incrementally after each
    # app's schema migrations. A data migration running mid-`migrate`, like this one,
    # would otherwise see an empty/incomplete Permission table. Force-create them now.
    from django.apps import apps as global_apps
    from django.contrib.auth.management import create_permissions

    for app_config in global_apps.get_app_configs():
        create_permissions(app_config, verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    admin_role, _ = Group.objects.get_or_create(name="Admin")
    editor_role, _ = Group.objects.get_or_create(name="Editor")
    Group.objects.get_or_create(name="User")

    all_perms = Permission.objects.all()
    admin_role.permissions.set(all_perms)
    editor_role.permissions.set(all_perms.exclude(codename__in=EDITOR_EXCLUDED_CODENAMES))
    # "User" role starts with no elevated permissions — content permissions land with
    # Phase 2's Page/Post models, at which point this role gets author-level access.


def unseed_roles(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Admin", "Editor", "User"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("users", "0001_initial"),
        ("settings_app", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_roles, unseed_roles),
    ]
