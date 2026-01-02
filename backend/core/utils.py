from django.db import transaction, IntegrityError


def auto_code(prefix: str, model, field: str, width: int) -> str:
    """
    Generate the next unique code for `model` based on `field` values
    that start with `prefix-`.

    Returns a string like f"{prefix}-{n:0{width}}".

    NOTE: This function does a best-effort read of the last code. Callers
    should wrap save() in a retry loop and handle IntegrityError to avoid
    race conditions in high-concurrency environments.
    """
    last = (
        model.objects
        .filter(**{f"{field}__startswith": f"{prefix}-"})
        .order_by(f"-{field}")
        .first()
    )

    if last:
        last_val = getattr(last, field)
        try:
            n = int(last_val.split("-")[-1]) + 1
        except Exception:
            n = 1
    else:
        n = 1

    return f"{prefix}-{str(n).zfill(width)}"


def generate_and_set_code(instance, prefix: str, field: str, width: int):
    """
    Helper wrapper that attempts to generate a code and set it on the
    instance. It does not save the instance.
    """
    if getattr(instance, field):
        return getattr(instance, field)

    Model = instance.__class__

    # Best-effort attempt — actual save should handle IntegrityError retries.
    code = auto_code(prefix, Model, field, width)
    setattr(instance, field, code)
    return code
