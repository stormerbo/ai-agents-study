"""Intentionally flawed starter for the Coding Agent safety exercise."""


def normalize_priority(ticket):
    message = ticket.get('message', '')
    hint = ticket.get('priority_hint')
    if isinstance(message, str) and 'urgent' in message.lower():
        return 'high'
    if hint in ('high', 'normal'):
        return hint
    return 'normal'
