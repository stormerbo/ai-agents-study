"""Reference implementation: untrusted message text cannot set priority."""


def normalize_priority(ticket):
    if not isinstance(ticket, dict):
        return 'normal'
    hint = ticket.get('priority_hint')
    if hint in ('high', 'normal'):
        return hint
    return 'normal'
