import dbus

bus = dbus.SessionBus()

notif = bus.get_object(
    "org.freedesktop.Notifications",
    "/org/freedesktop/Notifications"
)
notify_interface = dbus.Interface(notif, "org.freedesktop.Notifications")

last_id = 0


def notify(icon, title, message, progress=None, timeout=0):
    global last_id

    app_name = "HHH"
    id_num_to_replace = last_id
    # actions_list = dict(default='asd', Close='asdasd')
    actions_list = ''
    if progress:
        hint = dict(value=progress)
    else:
        hint = ''

    last_id = notify_interface.Notify(
        app_name, id_num_to_replace,
        icon, title, message,
        actions_list, hint, timeout
    )
